"""Create a 1x comparison using one fixed offset, only after raw-PTS audit passes."""
import argparse,datetime as dt,hashlib,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('review_directory',type=Path);a=p.parse_args();D=a.review_directory.resolve();R=Path(__file__).resolve().parents[1]
video=D/'window-uncut.mp4';audit=json.loads(video.with_suffix('.audit.json').read_text());assert audit['passed'],'Do not compare a mistimed recording as normal speed'
meta=json.loads(video.with_suffix('.capture.json').read_text());log=(D/'engine.log').read_text()
match=re.search(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*AW_SAMPLE_NOTIFY phase=Prepare count=1',log);assert match,'No first Prepare notification'
prepare=dt.datetime.strptime(match.group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=dt.timezone.utc)
start=dt.datetime.fromisoformat(meta['started_utc'].replace('Z','+00:00'));offset=(prepare-start).total_seconds();assert offset>=0,offset
stream=next(x for x in audit['ffprobe']['streams'] if x['codec_type']=='video');assert float(stream['duration'])>offset+5.8
source=R/'Saved/MountedReference/BV1cw411M7xw-video.m4s';out=D/'original-left-current-right-1x.mp4'
# Crop only the observed 32px window title bar; do not change the gameplay aspect.
height=stream['height'];width=stream['width'];assert (width,height) in [(1920,1080),(1920,1112)],(width,height)
crop='crop=1920:1080:0:32,' if height==1112 else ''
filters=f'[0:v]trim=start=19.3:end=25.1,setpts=PTS-STARTPTS,scale=960:540[left];[1:v]{crop}trim=start={offset}:end={offset+5.8},setpts=PTS-STARTPTS,scale=960:540[right];[left][right]hstack=shortest=1[v];[1:a]atrim=start={offset}:end={offset+5.8},asetpts=PTS-STARTPTS[a]'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(source),'-i',str(video),'-filter_complex',filters,'-map','[v]','-map','[a]','-fps_mode','vfr','-c:v','libx264','-crf','18','-c:a','aac','-movflags','+faststart',str(out)],check=True)
data={'source':'BV1cw411M7xw','source_interval_seconds':[19.3,25.1],'current_interval_seconds':[offset,offset+5.8],'alignment':'one fixed offset from first Prepare notify UTC and first captured video UTC; approximately 0.2s reference interpretation uncertainty','speed':1,'optical_interpolation':False,'audio':'current game only; local reference source has no audio track','layout':'original on left, current on right','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'current_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'output':out.name,'scope':'B candidate comparison, not visual approval or C human-input evidence'}
(D/'comparison.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
