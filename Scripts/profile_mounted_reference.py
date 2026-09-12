"""Measure native UE CSV frame times at 1080p without internal image capture.
This is the explicit B charge fixture, followed by natural AI and a stationary
player. It is neither normal-input C testing nor proof of visual acceptance.
"""
import argparse,csv,datetime,json,subprocess,shutil,time,re
from pathlib import Path
from mounted_candidate_version import snapshot
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--collect',type=Path);args=p.parse_args()
R=Path(__file__).resolve().parents[1];O=args.collect.resolve() if args.collect else R/'Saved/MountedReferenceProduction/Performance'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');O.mkdir(parents=True,exist_ok=True)
csv_root=R/'Saved/Profiling/CSV';before=set(csv_root.glob('*.csv'))
if not args.collect:(O/'version.json').write_text(json.dumps(snapshot(),indent=2)+'\n')
cmd=[str(R/'Scripts/launch_mounted_charge_sample.command'),'-MountedReviewExternal','-MountedReviewRecord=charge','-MountedReviewStartDelay=5','-MountedReviewSeconds=60','-csvCaptureFrames=1200','-csvCompression=0','-ExecCmds=csvprofile EXITONCOMPLETION',f'-abslog={O}/engine.log']
code=0
if not args.collect:
    with (O/'console.log').open('w') as f:
        p=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
        try:code=p.wait(timeout=100)
        except subprocess.TimeoutExpired:
            p.terminate();p.wait(timeout=10);raise SystemExit('Native CSV profile did not finish; no performance result accepted.')
log=(O/'engine.log').read_text(errors='replace')
match=re.search(r'Capture Ended\. Writing CSV to file : (.+)',log);assert match,'No completed native CSV in engine log'
name=Path(match.group(1).strip()).name
roots=[csv_root,Path.home()/'Library/Application Support/Epic/UnrealEngine/5.8/Saved/Profiling/CSV']
files=[p/name for p in roots if (p/name).is_file()];assert code==0 and len(files)==1,(code,files)
shutil.copy2(files[0],O/'native-ue.csv')
rows=[]
csv.field_size_limit(16*1024*1024)
with files[0].open() as f:
    for row in csv.DictReader(f):
        try:ms=float(row['FrameTime'])
        except (KeyError,ValueError,TypeError):continue
        rows.append(row)
assert len(rows)>500,len(rows)
# Preserve all CSV rows; separately report the tail after a declared warmup.
sample=rows[300:];metrics={}
for key in sample[0]:
    if key not in ['FrameTime','GameThreadTime','RenderThreadTime','RHIThreadTime','GPUTime','GPU/FrameTime','GPU Frame','GPU Frame Time']:continue
    values=[]
    for row in sample:
        try:values.append(float(row[key]))
        except (TypeError,ValueError):pass
    if not values:continue
    values.sort();metrics[key]={'samples':len(values),'mean_ms':sum(values)/len(values),'p50_ms':values[int((len(values)-1)*.5)],'p95_ms':values[int((len(values)-1)*.95)],'p99_ms':values[int((len(values)-1)*.99)]}
result={'scope':__doc__,'exit_code':code,'requested_resolution':[1920,1080],'internal_viewport_capture':False,'csv_columns':list(sample[0]),'excluded_warmup_frames':300,'raw_rows':len(rows),'metrics':metrics,'directory':str(O)}
(O/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
