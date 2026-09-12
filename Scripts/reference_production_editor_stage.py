"""One editor lifetime for owned reference assets, with ordinary deferred shutdown."""
import runpy,os,unreal as u,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1]
# Each child schedules the same delayed exit. They run synchronously before Slate
# ticks; the first callback requests normal exit only after all children finish.
os.environ['ASHWELL_REFERENCE_REUSE_ASSETS']='1'
os.environ['ASHWELL_REFERENCE_CHAINED']='1'
runpy.run_path(str(R/'Scripts/build_mounted_reference_environment.py'),run_name='__main__')
runpy.run_path(str(R/'Scripts/import_mounted_reference_animation.py'),run_name='__main__')
runpy.run_path(str(R/'Scripts/audit_mounted_reference_surface.py'),run_name='__main__')

u.EditorPythonScripting.set_keep_python_script_alive(True);finish=time.monotonic()
def quit_ready(dt):
    if time.monotonic()-finish>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(quit_ready)
