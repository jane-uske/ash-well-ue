#!/usr/bin/env python3
"""Record the actual UE viewport through the explicit A/B fixture export mode.
This is not ordinary input or natural-AI acceptance. No desktop input is injected.
"""
import argparse,subprocess,json,hashlib,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('mode',choices=['asset','charge']);a=p.parse_args()
R=Path(__file__).resolve().parents[1];records=R/'Saved/MountedBoss/Recordings';before=set(records.glob('*'))
out=R/'Docs/Verification/MountedChargeSample'/('A' if a.mode=='asset' else 'B');out.mkdir(exist_ok=True)
engine='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor'
flags=['-MountedAssetReview','-MountedReviewOrbit'] if a.mode=='asset' else ['-MountedChargeSample']
cmd=[engine,str(R/'AshWell.uproject'),'/Game/AshWell/MountedBoss/L_MountedCourtyard','-game','-windowed','-ResX=1280','-ResY=720','-NoSplash','-CombatPrototype','-MountedExperiment','-MountedDebug','-DisablePlugins=AllToolsets,ModelContextProtocol',f'-MountedReviewRecord={a.mode}',f'-abslog={out}/current-{a.mode}-engine.log',*flags]
import os
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode-beta.app/Contents/Developer')
with (out/f'current-{a.mode}-console.log').open('w') as log:
    proc=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:code=proc.wait(timeout=100)
    except subprocess.TimeoutExpired:
        proc.terminate();proc.wait(timeout=10);raise SystemExit('Recording did not complete; no clip accepted.')
new=[x for x in records.glob('*') if x not in before and (x/'recording.json').exists()]
assert code==0 and len(new)==1,(code,new)
d=new[0];meta=json.loads((d/'recording.json').read_text());assert meta.get('frame_write_failures')==0,meta
assert meta['review_fixture']==a.mode and meta['frames_written']>100,meta
silent=not meta.get('audio_wav_complete',False)
if silent:print('SILENT_PREVIEW: audio was not completed; this is an A/B visual preview only.',flush=True)
dest=out/(f'current-{a.mode}-uncut'+('-silent' if silent else '')+'.mp4')
subprocess.run(['python3',str(R/'Scripts/assemble_mounted_recording.py'),str(d),'--output',str(dest)]+(['--video-only-preview'] if silent else []),check=True)
summary=json.loads((d/'review.json').read_text());summary['recording_directory']=str(d);summary['video']=str(dest);summary['audio_missing']=silent;summary['module_sha256']=hashlib.sha256((R/'Binaries/Mac/libUnrealEditor-AshWell.dylib').read_bytes()).hexdigest();summary['scope']='A/B project render export. Not a C normal-input combat recording.'
(out/f'current-{a.mode}-verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
