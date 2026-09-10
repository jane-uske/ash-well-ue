"""One-session import helper; only reruns the explicitly edited trial script."""
import unreal as u, traceback, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'Scripts/build_animation_trial.py'
u.EditorPythonScripting.set_keep_python_script_alive(True)
last=None
def tick(dt):
    global last
    stamp=SCRIPT.stat().st_mtime
    if stamp==last:return
    last=stamp
    try:exec(compile(SCRIPT.read_text(),str(SCRIPT),'exec'),{'__file__':str(SCRIPT)})
    except Exception:
        text=traceback.format_exc();u.log_error(text)
        (ROOT/'Saved/AnimationTrial/import-error.txt').write_text(text)
handle=u.register_slate_post_tick_callback(tick)
