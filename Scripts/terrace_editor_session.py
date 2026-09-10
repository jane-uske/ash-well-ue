"""Local one-session queue exclusively for the new Terrace level; no shared queue."""
from pathlib import Path
import unreal as u, json, traceback, time
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Saved/Terrace'; OUT.mkdir(parents=True,exist_ok=True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
last=None

def tick(dt):
 global last
 job=OUT/'editor-job.json'
 if not job.exists():return
 stamp=job.stat().st_mtime_ns
 if stamp==last:return
 last=stamp;data=json.loads(job.read_text());result={'id':data['id'],'ok':False}
 try:
  script=(ROOT/'Scripts'/data['script']).resolve()
  assert script.parent==ROOT/'Scripts' and script.name.startswith('terrace_') and script.suffix=='.py'
  exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script)})
  result['ok']=True
 except Exception:
  result['error']=traceback.format_exc();u.log_error(result['error'])
 (OUT/'editor-result.json').write_text(json.dumps(result,indent=2))
handle=u.register_slate_post_tick_callback(tick)
(OUT/'editor-ready.json').write_text(json.dumps({'engine':u.SystemLibrary.get_engine_version(),'pid':__import__('os').getpid()}))
