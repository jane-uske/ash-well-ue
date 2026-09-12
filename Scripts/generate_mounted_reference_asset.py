#!/usr/bin/env python3
"""Compose the installed Meshy CLI; keep the approved batch budget and originals."""
import argparse
import base64
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('/Users/rare/.codex/plugins/cache/openai-curated-remote/meshy-openai-plugin/0.4.1/skills/meshy-3d-generation')
CLI = SKILL / 'scripts/meshy_task.py'
LEDGER = ROOT / 'Docs/Implementation/MountedBoss/ChargeSample/meshy-reference-budget.json'
ENDPOINT = '/openapi/v1/image-to-3d'
EXPECTED_COST = 35
ASSETS = {
    'wall': {'name': 'reference-ruin-wall', 'dimensions_cm': [400, 65, 260]},
    'rock': {'name': 'reference-flat-rock', 'dimensions_cm': [330, 210, 65]},
    'stake': {'name': 'reference-roadside-stake', 'dimensions_cm': [140, 25, 400]},
    'castle': {'name': 'reference-distant-fortress', 'dimensions_cm': [9000, 3000, 5500]},
}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('asset', choices=ASSETS)
    p.add_argument('reference', type=Path)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    image = a.reference.resolve()
    assert image.is_file() and image.suffix.lower() == '.png'
    os.chdir(ROOT)
    # The user explicitly supplied this exact file. The credential stays in the
    # child environment; no copied .env, command-line secret, or logged prefix.
    env = dict(os.environ, MESHY_API_KEY=Path('/Users/rare/blender/.env').read_text().strip())

    def cli(*args, visible=False):
        if visible:
            proc = subprocess.Popen([sys.executable, str(CLI), *map(str, args)], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                if 'API key loaded:' not in line and 'READY: key=' not in line:
                    print(line, end='', flush=True)
            if proc.wait():
                raise RuntimeError(f'Meshy CLI {args[0]} failed; preserve the task ID before recovery.')
            return ''
        r = subprocess.run([sys.executable, str(CLI), *map(str, args)], env=env, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f'Meshy CLI {args[0]} failed (exit {r.returncode}); do not resubmit uncertain paid tasks.')
        return r.stdout.strip()

    assert 'READY: key=' in cli('check-env'), 'Meshy environment is not ready'
    balance = json.loads(cli('balance'))['balance']
    spec = ASSETS[a.asset]
    lock_path = ROOT / 'Saved/MountedReferenceProduction/meshy.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(LEDGER.read_text()) if LEDGER.exists() else {
            'approved_total_cap': 964, 'first_batch_cap': 200,
            'initial_balance': 2364, 'permanent_balance_floor': 1400,
            'pricing_source': 'https://help.meshy.ai/en/articles/16815622-how-many-credits-does-each-meshy-api-task-cost',
            'assets': {},
        }
        entry = data['assets'].get(a.asset)
        if entry and not entry.get('task_id'):
            raise RuntimeError('Previous submission has an uncertain outcome. Reconcile it before any retry.')
        if entry and entry.get('status') == 'downloaded':
            print(json.dumps(entry, ensure_ascii=False)); return
        if not entry:
            allocated = sum(e.get('consumed_credits', e['reserved_credits']) for e in data['assets'].values())
            assert allocated + EXPECTED_COST <= min(data['first_batch_cap'], data['approved_total_cap']), 'Approved budget exhausted'
            assert balance - EXPECTED_COST >= data['permanent_balance_floor'], 'Would consume reserved permanent credits'
            print(json.dumps({'asset': a.asset, 'balance': balance, 'reserved': EXPECTED_COST,
                              'batch_allocated_after': allocated + EXPECTED_COST, 'dry_run': a.dry_run}), flush=True)
            if a.dry_run: return
            entry = dict(spec, status='submitting', reserved_credits=EXPECTED_COST,
                         reference_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                         submitted_utc=dt.datetime.now(dt.timezone.utc).isoformat())
            data['assets'][a.asset] = entry
            save(LEDGER, data)
            request_dir = ROOT / 'meshy_output/reference-production-requests'
            request_dir.mkdir(parents=True, exist_ok=True)
            request = request_dir / f'task_request_{a.asset}.json'
            save(request, {'image_url': 'data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode(),
                           'model_type': 'standard', 'ai_model': 'meshy-7', 'ultra_mode': True,
                           'should_texture': True, 'enable_pbr': True, 'texture_resolution': '4k',
                           'should_remesh': True, 'target_polycount': 30000, 'topology': 'triangle',
                           'save_pre_remeshed_model': True, 'image_enhancement': False, 'target_formats': ['glb']})
            task_id = cli('create', '--endpoint', ENDPOINT, '--payload-file', request).splitlines()[-1]
            directory = Path(cli('project-dir', '--task-id', task_id, '--prompt', spec['name']).splitlines()[-1])
            shutil.copy2(image, directory / 'reference.png')
            entry.update(task_id=task_id, project_dir=str(directory.relative_to(ROOT)), status='submitted')
            save(LEDGER, data)
        directory = ROOT / entry['project_dir']
        task_id = entry['task_id']

    cli('poll', '--endpoint', ENDPOINT, '--task-id', task_id, '--timeout', 1200, '--project-dir', directory, visible=True)
    task_file = directory / f'task_{task_id}.json'
    task = json.loads(task_file.read_text())
    cli('download', '--task-json', task_file, '--format', 'glb', '--output', directory / 'model.glb', visible=True)
    cli('thumbnail', '--project-dir', directory, '--task-json', task_file, visible=True)
    downloaded = ['model.glb', 'reference.png', 'thumbnail.png']
    for material, maps in enumerate(task.get('texture_urls', [])):
        for kind, url in maps.items():
            if not isinstance(url, str) or not url.startswith('https://'): continue
            filename = f'texture_{material}_{kind}.png'
            cli('download', '--url', url, '--output', directory / filename, visible=True)
            downloaded.append(filename)
    balance_after = json.loads(cli('balance'))['balance']
    with lock_path.open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(LEDGER.read_text())
        entry = data['assets'][a.asset]
        consumed = task.get('consumed_credits')
        assert isinstance(consumed, (int, float)), 'Task did not report its actual credit cost'
        entry.update(status='downloaded', consumed_credits=consumed, balance_after=balance_after,
                     files={name: {'bytes': (directory/name).stat().st_size,
                                   'sha256': hashlib.sha256((directory/name).read_bytes()).hexdigest()}
                            for name in downloaded if (directory/name).is_file()})
        cli('record', '--project-dir', directory, '--task-id', task_id, '--task-type', 'image-to-3d',
            '--stage', 'downloaded', '--files', ','.join(downloaded))
        save(LEDGER, data)
        save(directory / 'asset-manifest.json', entry)
        print(json.dumps({'asset': a.asset, 'task_id': task_id, 'project_dir': entry['project_dir'],
                          'consumed_credits': consumed, 'balance_after': balance_after}), flush=True)


if __name__ == '__main__':
    main()
