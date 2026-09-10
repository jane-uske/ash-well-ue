"""Explicit local import session, watching only Saved/Polish/editor-job.json."""
import unreal as u,json,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];JOB=ROOT/'Saved/Polish/editor-job.json'
u.EditorPythonScripting.set_keep_python_script_alive(True)
last=None
def tick(dt):
 global last
 if not JOB.exists():return
 stamp=JOB.stat().st_mtime_ns
 if stamp==last:return
 last=stamp;job=json.loads(JOB.read_text());report={'id':job['id'],'ok':False}
 try:
  script=(ROOT/job['script']).resolve()
  assert script.parent==ROOT/'Scripts'
  exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script)})
  report['ok']=True
 except Exception:report['error']=traceback.format_exc();u.log_error(report['error'])
 (ROOT/'Saved/Polish/editor-result.json').write_text(json.dumps(report,indent=2))
handle=u.register_slate_post_tick_callback(tick)
