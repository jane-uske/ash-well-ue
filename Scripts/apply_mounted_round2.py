from pathlib import Path
import runpy,os,json,traceback
import unreal as u
R=Path(__file__).resolve().parents[1]
os.environ['ASHWELL_ROUND2_CHAINED']='1'
try:
 for script,report in [('import_mounted_charge_round2.py','visual-import.json'),('tune_mounted_readability_round2.py','readability.json')]:
  runpy.run_path(str(R/'Scripts'/script),run_name='__main__')
  assert json.loads((R/'Saved/MountedChargeRound2'/report).read_text())['passed'],report
 u.log('ROUND2_APPLY_COMPLETE')
except Exception:u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
