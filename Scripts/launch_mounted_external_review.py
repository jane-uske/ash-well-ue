"""A/B fixture without viewport readback; QuickRecorder captures the real window.
Never use this entry as a normal-input human C test.
"""
import argparse,json,os,subprocess,datetime
from pathlib import Path
from mounted_candidate_version import snapshot
p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['asset','charge','death']);p.add_argument('--delay',type=float,default=40);p.add_argument('--seconds',type=float,default=25);a=p.parse_args()
R=Path(__file__).resolve().parents[1];O=R/'Saved/MountedReferenceProduction/External'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');O.mkdir(parents=True)
(O/'version.json').write_text(json.dumps(snapshot(),indent=2)+'\n')
cmd=[str(R/'Scripts/launch_mounted_charge_sample.command'),'-MountedReviewExternal',f'-MountedReviewRecord={a.mode}',f'-MountedReviewStartDelay={a.delay}',f'-MountedReviewSeconds={a.seconds}',f'-abslog={O}/engine.log']
if a.mode!='charge':cmd+=['-MountedAssetReview','-MountedReviewOrbit']
print(json.dumps({'scope':'external A/B fixture, not C','directory':str(O),'command':cmd}),flush=True)
with (O/'console.log').open('w') as f:
    proc=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
    (O/'process.json').write_text(json.dumps({'pid':proc.pid,'scope':'owned A/B review process'},indent=2)+'\n')
    try:code=proc.wait(timeout=a.delay+a.seconds+70)
    except subprocess.TimeoutExpired:
        proc.terminate();proc.wait(timeout=10);raise SystemExit('Review timeout; preserve external recording and engine log.')
print(json.dumps({'exit_code':code,'directory':str(O)}),flush=True)
raise SystemExit(code)
