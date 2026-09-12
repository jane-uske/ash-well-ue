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
    if not args.preflight:
        from mounted_capture_environment import require_unlocked
        require_unlocked()
        recorder=ROOT/'Saved/MountedReferenceProduction/record_mounted_window'
        recorder_source=ROOT/'Scripts/record_mounted_window.swift'
        if not recorder.exists() or recorder.stat().st_mtime<recorder_source.stat().st_mtime:
            subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-O',str(recorder_source),'-o',str(recorder)],check=True)
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
              'command': command, 'video': None, 'video_status': 'awaiting native window recording',
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
    print('本入口会自动录制15分钟游戏窗口与游戏音频，麦克风关闭；请等“录像已开始”再按E。不要按F8。', flush=True)
    print('E 入战 / WASD 移动 / Tab 锁定 / 空格跳跃 / Shift 短按闪避、长按冲刺 / 左右键攻击 / R 重试。', flush=True)
    print('正常试玩 10–15 分钟后退出游戏；不使用数字选招和 F1–F8 调试键。', flush=True)
    started = time.monotonic()
    capture_proc=None;capture_log=None
    with (folder/'console.log').open('w') as output:
        proc = subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-beta.app/Contents/Developer'),stdout=output,stderr=subprocess.STDOUT)
        report['pid'] = proc.pid
        write(folder/'session.json',report)
        try:
            if args.preflight:
                try:code=proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    proc.terminate();code=proc.wait(timeout=10)
            else:
                until=time.monotonic()+40
                while time.monotonic()<until:
                    log=(folder/'engine.log').read_text(errors='replace') if (folder/'engine.log').exists() else ''
                    if 'AW_SAMPLE_RIG ready=1' in log:break
                    if proc.poll() is not None:raise RuntimeError('游戏未完成启动；保留日志。')
                    time.sleep(.25)
                else:raise RuntimeError('等待游戏窗口超时。')
                capture_log=(folder/'capture.log').open('w')
                capture_proc=subprocess.Popen([str(recorder),str(proc.pid),str(folder/'human-window-uncut.mp4'),'900'],stdout=capture_log,stderr=subprocess.STDOUT)
                until=time.monotonic()+20
                while time.monotonic()<until:
                    text=(folder/'capture.log').read_text(errors='replace')
                    if 'NATIVE_RECORDING_STARTED' in text:break
                    if capture_proc.poll() is not None:raise RuntimeError('原生录像未启动，不能把本次认定为C初测；详见capture.log。')
                    time.sleep(.2)
                else:raise RuntimeError('等待首个录像画面超时；本次C准备阻塞。')
                report['video']=str(folder/'human-window-uncut.mp4');report['video_status']='recording_pending_audit'
                report['recorder_sha256']=hashlib.sha256(recorder.read_bytes()).hexdigest();write(folder/'session.json',report)
                print('录像已开始。现在可以按E，用正式按键试玩10–15分钟；结束后正常退出游戏。',flush=True)
                code = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:
                code = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill();code=proc.wait()
        except Exception as error:
            report['preparation_error']=str(error);report['video_status']='blocked';print(str(error),flush=True)
            if proc.poll() is None:proc.terminate()
            code=proc.wait(timeout=10)
        finally:
            if capture_proc and capture_proc.poll() is None:
                capture_proc.terminate()
                try:capture_proc.wait(timeout=25)
                except subprocess.TimeoutExpired:capture_proc.kill();capture_proc.wait()
            if capture_log:capture_log.close()
            if capture_proc:
                report['recorder_exit_code']=capture_proc.returncode
                video=folder/'human-window-uncut.mp4'
                if video.exists() and video.with_suffix('.capture.json').exists():
                    audit=subprocess.run(['python3',str(ROOT/'Scripts/audit_mounted_native_capture.py'),str(video)],capture_output=True,text=True)
                    (folder/'capture-audit.log').write_text(audit.stdout+audit.stderr)
                    report['video_status']='audit_passed_pending_human_review' if audit.returncode==0 else 'audit_failed'
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
    return 0 if code == 0 and not report['fatal_or_ensure'] and not report.get('preparation_error') else 1


if __name__ == '__main__':
    raise SystemExit(main())
