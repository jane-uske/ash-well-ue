"""Local editor session helper. Runs only explicitly queued scripts in Scripts/.

Start via -ExecutePythonScript=.../editor_session.py. No network listener and no
startup registration: ordinary project opens do not execute this helper.
"""
import json
import pathlib
import time
import traceback
import unreal

ROOT = pathlib.Path(__file__).resolve().parents[1]
SESSION = ROOT / 'Saved' / 'Automation'
SESSION.mkdir(parents=True, exist_ok=True)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
_last = None
_check = 0.0

def tick(delta):
    global _last, _check
    now = time.monotonic()
    if now - _check < 1.0:
        return
    _check = now
    queue = SESSION / 'job.json'
    if not queue.exists():
        return
    try:
        job = json.loads(queue.read_text())
        if job['id'] == _last:
            return
        _last = job['id']
        script = (ROOT / 'Scripts' / job['script']).resolve()
        if not script.is_relative_to(ROOT / 'Scripts') or script.suffix != '.py':
            raise ValueError('Only project Scripts/*.py jobs are accepted')
        result = {'id': _last, 'script': str(script), 'state': 'running'}
        (SESSION / 'result.json').write_text(json.dumps(result, indent=2))
        scope = {'__file__': str(script), '__name__': '__main__'}
        exec(compile(script.read_text(), str(script), 'exec'), scope)
        result['state'] = 'completed'
        (SESSION / 'result.json').write_text(json.dumps(result, indent=2))
    except Exception:
        error = traceback.format_exc()
        unreal.log_error(error)
        (SESSION / 'result.json').write_text(json.dumps({'id': _last, 'state': 'failed', 'error': error}, indent=2))

_handle = unreal.register_slate_post_tick_callback(tick)
(SESSION / 'ready.json').write_text(json.dumps({'engine': unreal.SystemLibrary.get_engine_version(), 'project': str(ROOT)}))
unreal.log('ASHWELL: local editor automation ready')
