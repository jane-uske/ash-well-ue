"""Capture a real UE A/B fixture using Apple's native recording output."""
import argparse,datetime,json,os,subprocess,time,shutil
from pathlib import Path
from mounted_candidate_version import snapshot
from mounted_capture_environment import require_unlocked
p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['asset','charge','death']);a=p.parse_args()
require_unlocked()
R=Path(__file__).resolve().parents[1];O=R/'Docs/Verification/MountedChargeSample/ReferenceProduction'/('Native-'+a.mode+'-'+datetime.datetime.now().strftime('%H%M%S'));O.mkdir(parents=True)
binary=R/'Saved/MountedReferenceProduction/record_mounted_window';source=R/'Scripts/record_mounted_window.swift'
if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-O',str(source),'-o',str(binary)],check=True)
(O/'version.json').write_text(json.dumps(snapshot(),indent=2)+'\n')
delay=3 if a.mode=='asset' else 15
cmd=[str(R/'Scripts/launch_mounted_charge_sample.command'),'-MountedReviewExternal',f'-MountedReviewRecord={a.mode}',f'-MountedReviewStartDelay={delay}','-MountedReviewSeconds=45',f'-abslog={O}/engine.log']
if a.mode!='charge':cmd+=['-MountedAssetReview','-MountedReviewOrbit']
with (O/'console.log').open('w') as f:
    proc=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
    try:
        until=time.monotonic()+45
        while time.monotonic()<until:
            log=(O/'engine.log').read_text(errors='replace') if (O/'engine.log').exists() else ''
            if 'AW_SAMPLE_RIG ready=1' in log:break
            if proc.poll() is not None:raise RuntimeError('UE exited before its sample rig was ready')
            time.sleep(.25)
        else:raise RuntimeError('UE did not become ready')
        with (O/'capture.log').open('w') as capture_log:
            result=subprocess.run([str(binary),str(proc.pid),str(O/'window-uncut.mp4'),'30'],stdout=capture_log,stderr=subprocess.STDOUT,timeout=55)
        assert result.returncode==0,'Native capture blocked; preserve logs and any partial file.'
        code=proc.wait(timeout=60);assert code==0,code
    finally:
        if proc.poll() is None:
            proc.terminate();proc.wait(timeout=10)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(O/'window-uncut.mp4')]))
(O/'ffprobe.json').write_text(json.dumps(probe,indent=2)+'\n')
video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
duration_gap=abs(float(video['duration'])-float(audio['duration']))
summary={'scope':'Native window recording of explicit A/B fixture, not human C','mode':a.mode,'pid':proc.pid,'module_and_assets':'version.json','video_seconds':float(video['duration']),'audio_seconds':float(audio['duration']),'duration_gap_seconds':duration_gap,'av_duration_gate_passed':duration_gap<.25,'cuts':0,'speed':1,'interpolation':False,'directory':str(O)}
(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
raise SystemExit(0 if summary['av_duration_gate_passed'] else 1)
