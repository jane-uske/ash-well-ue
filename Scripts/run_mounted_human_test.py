#!/usr/bin/env python3
"""Launch normal-input C initial testing; collect evidence without driving gameplay."""
import datetime as dt
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'AshWell.uproject'
ENGINE = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor')


def processes():
    text = subprocess.check_output(['ps', '-axo', 'pid,ppid,args'], text=True, errors='replace')
    result = []
    for row in text.splitlines()[1:]:
        parts = row.strip().split(None, 2)
        if len(parts) == 3:
            result.append((int(parts[0]), int(parts[1]), parts[2]))
    return result


def write(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    temp.replace(path)


def cleanup_reporters(owner_pid, directory):
    """Only this exited UE PID's orphan reporters; preserve reports first."""
    found = []
    crash_root = Path.home() / 'Library/Application Support/Epic/UnrealEngine/5.8/Saved/Crashes'
    for folder in crash_root.glob(f'*-UE-AshWell-pid-{owner_pid}-*'):
        target = directory / 'crashes' / folder.name
        shutil.copytree(folder, target, dirs_exist_ok=True)
        found.append(str(target))
    stopped = []
    marker = f'-UE-AshWell-pid-{owner_pid}-'
    for pid, parent, command in processes():
        if parent == 1 and command.startswith('CrashReportClient ') and marker in command:
            os.kill(pid, signal.SIGTERM)
            stopped.append(pid)
    return {'preserved_crash_directories': found, 'reporters_sent_sigterm': stopped}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight',action='store_true',help='20-second launch/exit check without any gameplay input; never C evidence.')
    args=parser.parse_args()
    live = [pid for pid, _, cmd in processes() if str(ENGINE) in cmd and str(PROJECT) in cmd]
    if live:
        raise SystemExit(f'AshWell 已有运行实例 {live}。本入口不会关闭它；请先正常退出该实例。')
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    folder = ROOT / 'Saved/MountedHumanTests' / stamp
    folder.mkdir(parents=True)
    debug_root = ROOT / 'Saved/MountedBoss/Debug'
    old_logs = set(debug_root.glob('*.jsonl'))
    command = [str(ENGINE), str(PROJECT), '/Game/AshWell/MountedBoss/L_MountedCourtyard',
               '-game', '-windowed', '-ResX=1920', '-ResY=1080', '-NoSplash',
               '-CombatPrototype', '-MountedExperiment', '-MountedChargeSample',
               '-MountedDebug', '-MountedFootPlacement', '-DisablePlugins=AllToolsets,ModelContextProtocol',
               f'-abslog={folder}/engine.log']
    report = {'scope': 'human C initial test; not final acceptance', 'status': 'running',
              'head': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'module_sha256': hashlib.sha256((ROOT/'Binaries/Mac/libUnrealEditor-AshWell.dylib').read_bytes()).hexdigest(),
              'command': command, 'video': None, 'video_status': 'awaiting external window recording',
              'input_source': 'human keyboard/mouse only', 'forced_attack': False,
              'boss_health_override': False, 'ai_frozen': False, 'time_scale_override': False,
              'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    if args.preflight:
        report['scope']='launcher preflight only; no human C test performed'
        report['input_source']='none; no input injected'
    report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (ROOT/'Source').rglob('*') if p.is_file() and p.suffix in ('.cpp','.h','.cs','.inl')}
    from mounted_candidate_version import snapshot
    write(folder/'version.json',snapshot())
    report['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(folder/'session.json', report)
    print(f'真人 C 初测日志：{folder}', flush=True)
    print('请用 QuickRecorder 录制 AshWell 窗口：应用音频开启、麦克风关闭。不要按 F8。', flush=True)
    print('E 入战 / WASD 移动 / Tab 锁定 / 空格跳跃 / Shift 短按闪避、长按冲刺 / 左右键攻击 / R 重试。', flush=True)
    print('正常试玩 10–15 分钟后退出游戏；不使用数字选招和 F1–F8 调试键。', flush=True)
    started = time.monotonic()
    with (folder/'console.log').open('w') as output:
        proc = subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-beta.app/Contents/Developer'),stdout=output,stderr=subprocess.STDOUT)
        report['pid'] = proc.pid
        write(folder/'session.json',report)
        try:
            if args.preflight:
                try:code=proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    proc.terminate();code=proc.wait(timeout=10)
            else:code = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:
                code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill();code=proc.wait()
    report['elapsed_wall_seconds'] = time.monotonic()-started
    report['exit_code'] = code
    report['status'] = 'ended_review_pending'
    report['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (folder/'debug').mkdir()
    event_files = []
    for path in debug_root.glob('*.jsonl'):
        if path not in old_logs:
            shutil.copy2(path,folder/'debug'/path.name)
            event_files.append(path.name)
    report['debug_logs'] = event_files
    log = (folder/'engine.log').read_text(errors='replace') if (folder/'engine.log').exists() else ''
    report['fatal_or_ensure'] = bool(re.search(r'Fatal error:|Assertion failed:|Ensure condition failed:',log))
    report['cleanup'] = cleanup_reporters(proc.pid,folder)
    write(folder/'session.json',report)
    print(f'初测记录已保存，等待录像和真人反馈：{folder}',flush=True)
    return 0 if code == 0 and not report['fatal_or_ensure'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
