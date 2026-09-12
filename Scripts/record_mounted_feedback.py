"""Uncut native-window recordings of explicit sword-hit/shield-block fixtures, not C."""
from pathlib import Path
import datetime,json,subprocess,time
from mounted_candidate_version import snapshot
from mounted_capture_environment import require_unlocked
require_unlocked();R=Path(__file__).resolve().parents[1]
O=R/'Docs/Verification/MountedChargeSample/SyncSizeSoundMoves'/('Feedback-'+datetime.datetime.now().strftime('%H%M%S'));O.mkdir(parents=True)
(O/'version.json').write_text(json.dumps(snapshot(),indent=2)+'\n')
for case in ['light','shield_block']:
    D=O/case;D.mkdir();cmd=[str(R/'Scripts/launch_mounted_boss_current.command'),'-MountedQA','-MountedDebug',f'-MountedProbe={case}',f'-abslog={D}/engine.log']
    with (D/'console.log').open('w') as log:
        proc=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                text=(D/'engine.log').read_text(errors='replace') if (D/'engine.log').exists() else ''
                if 'AW_SAMPLE_RIG ready=1' in text:break
                if proc.poll() is not None:raise RuntimeError('UE exited before recording')
                time.sleep(.15)
            else:raise RuntimeError('UE readiness timeout')
            with (D/'capture.log').open('w') as capture:
                subprocess.run([str(R/'Saved/MountedReferenceProduction/record_mounted_window'),str(proc.pid),str(D/'window-uncut.mp4'),'8'],stdout=capture,stderr=subprocess.STDOUT,timeout=25,check=True)
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
    subprocess.run(['python3',str(R/'Scripts/audit_mounted_native_capture.py'),str(D/'window-uncut.mp4')],check=True)
    (D/'scope.json').write_text(json.dumps({'fixture':case,'input':'Explicit QA calls to ordinary attack action, not keyboard input','duration':8,'cuts':0,'speed':1,'player_unchanged':True,'boss_hp':900,'owned_process_exit':proc.returncode},indent=2)+'\n')
print(O,flush=True)
