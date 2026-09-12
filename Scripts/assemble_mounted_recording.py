#!/usr/bin/env python3
"""Encode every captured UE viewport frame at its original timestamp with master audio.
No cuts, speed changes, synthetic frames or gameplay intervention. Gaps hold the previous frame.
"""
import argparse,json,subprocess,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--output',type=Path);p.add_argument('--video-only-preview',action='store_true',help='Explicit silent A/B preview; never a complete audiovisual combat handoff.');a=p.parse_args()
d=a.directory.resolve();meta=json.loads((d/'recording.json').read_text())
if meta.get('status') not in ('saved','saved_with_gaps') and not (a.video_only_preview and meta.get('frame_write_failures')==0 and meta.get('frames_written',0)>1):raise SystemExit('Recording is not fully saved; inspect recording.json before delivery.')
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
audio_complete=wav.exists() and meta.get('audio_wav_complete') is True
if not audio_complete and not a.video_only_preview:raise SystemExit('Game audio export was not completed.')
use_audio=audio_complete and not a.video_only_preview
output=(a.output or d/'uncut-gameplay.mp4').resolve();output.parent.mkdir(parents=True,exist_ok=True)
cmd=[ffmpeg,'-y','-hide_banner','-loglevel','warning','-safe','0','-f','concat','-i',str(d/'frames.ffconcat')]
if use_audio:cmd+=['-i',str(wav)]
cmd+=['-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-fps_mode','vfr','-t',str(meta['duration_seconds']),'-movflags','+faststart']
if use_audio:cmd+=['-c:a','aac','-b:a','160k']
cmd+=[str(output)];subprocess.run(cmd,check=True)
report={**meta,'requested_frames':len(requested),'saved_frames':len(frames),'missing_frames':len(requested)-len(frames),'max_capture_gap_seconds':max(frames[i+1]['real_seconds']-frames[i]['real_seconds'] for i in range(len(frames)-1)),'audio_present':use_audio,'video_only_preview':a.video_only_preview,'source_audio_complete':audio_complete,'output':str(output),'cuts':0,'speed':1,'known_limit':'Capture may reduce runtime performance; timestamp gaps hold the previous captured frame. Video-only previews do not meet a complete audiovisual combat handoff.'}
(output.with_suffix('.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
