#!/usr/bin/env python3
"""Encode every captured UE viewport frame at its original timestamp with master audio.
No cuts, speed changes, synthetic frames or gameplay intervention. Gaps hold the previous frame.
"""
import argparse,json,subprocess,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
d=a.directory.resolve();meta=json.loads((d/'recording.json').read_text())
if meta.get('status') not in ('saved','saved_with_gaps'):raise SystemExit('Recording is not fully saved; inspect recording.json before delivery.')
requested=[json.loads(x) for x in (d/'frames.jsonl').read_text().splitlines()];frames=[x for x in requested if (d/x['file']).exists()]
if len(frames)<2:raise SystemExit('Not enough actual frames; recording not deliverable.')
ffmpeg=shutil.which('ffmpeg')
if not ffmpeg:raise SystemExit('ffmpeg unavailable')
lines=['ffconcat version 1.0']
for i,f in enumerate(frames):
    end=frames[i+1]['real_seconds'] if i+1<len(frames) else meta['duration_seconds']
    start=0 if i==0 else f['real_seconds']
    lines+=['file '+"'"+f['file']+"'",f'duration {max(.001,end-start):.6f}']
lines+=['file '+"'"+frames[-1]['file']+"'"]
(d/'frames.ffconcat').write_text('\n'.join(lines)+'\n')
wav=d/'game-audio.wav'
if not wav.exists() or not meta.get('audio_wav_complete'):raise SystemExit('Game audio export was not completed.')
output=(a.output or d/'uncut-gameplay.mp4').resolve();output.parent.mkdir(parents=True,exist_ok=True)
cmd=[ffmpeg,'-y','-hide_banner','-loglevel','warning','-safe','0','-f','concat','-i',str(d/'frames.ffconcat')]
if wav.exists():cmd+=['-i',str(wav)]
cmd+=['-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-fps_mode','vfr','-t',str(meta['duration_seconds']),'-movflags','+faststart']
if wav.exists():cmd+=['-c:a','aac','-b:a','160k']
cmd+=[str(output)];subprocess.run(cmd,check=True)
report={**meta,'requested_frames':len(requested),'saved_frames':len(frames),'missing_frames':len(requested)-len(frames),'max_capture_gap_seconds':max(frames[i+1]['real_seconds']-frames[i]['real_seconds'] for i in range(len(frames)-1)),'audio_present':wav.exists(),'output':str(output),'cuts':0,'speed':1,'known_limit':'Capture may reduce runtime performance; timestamp gaps hold the previous captured frame.'}
(output.with_suffix('.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
