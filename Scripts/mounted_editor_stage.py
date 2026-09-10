from pathlib import Path
import unreal as u,runpy,traceback,json
R=Path(__file__).resolve().parents[1];O=R/'Saved/MountedBoss';O.mkdir(exist_ok=True,parents=True)
try:
 runpy.run_path(str(R/'Scripts/import_mounted_assets.py'),run_name='__main__')
 runpy.run_path(str(R/'Scripts/import_mounted_rider.py'),run_name='__main__')
 runpy.run_path(str(R/'Scripts/build_mounted_arena.py'),run_name='__main__')
 runpy.run_path(str(R/'Scripts/tune_mounted_arena.py'),run_name='__main__')
 (O/'editor-stage.json').write_text(json.dumps({'passed':True}))
except Exception:
 (O/'editor-stage.json').write_text(json.dumps({'passed':False,'error':traceback.format_exc()}));u.log_error(traceback.format_exc())
u.SystemLibrary.quit_editor()
