import unreal as u,runpy,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1]
try:runpy.run_path(str(R/'Scripts/import_mounted_rider.py'),run_name='__main__')
except Exception:u.log_error(traceback.format_exc())
u.SystemLibrary.quit_editor()
