"""Check raw capture PTS against host time and the encoded media; never retime."""
import argparse,csv,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video',type=Path);a=p.parse_args();video=a.video.resolve()
meta=json.loads(video.with_suffix('.capture.json').read_text())
rows=list(csv.DictReader(video.with_suffix('.samples.csv').open()));result={'scope':__doc__,'capture':meta,'streams':{}}
for kind in ['video','audio']:
    samples=[r for r in rows if r['type']==kind and r['appended']=='true'];assert len(samples)>1,kind+' has no completed source samples'
    pts=[int(s['pts_value'])/int(s['pts_timescale']) for s in samples];host=[float(s['host_seconds']) for s in samples]
    result['streams'][kind]={'buffers':len(samples),'first_pts':pts[0],'last_pts':pts[-1],'pts_span':pts[-1]-pts[0],'host_span':host[-1]-host[0],'host_clock_error':abs((pts[-1]-pts[0])-(host[-1]-host[0])),'monotonic':all(b>=a for a,b in zip(pts,pts[1:])),'maximum_gap_seconds':max(b-a for a,b in zip(pts,pts[1:]))}
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));result['ffprobe']=probe
v=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
sv=result['streams']['video'];sa=result['streams']['audio']
checks={'video_clock_matches_host':sv['host_clock_error']<.15,'audio_clock_matches_host':sa['host_clock_error']<.15,'timestamps_monotonic':sv['monotonic'] and sa['monotonic'],'encoded_video_preserves_pts':abs(float(v['duration'])-sv['pts_span'])<.15,'av_duration_agrees':abs(float(v['duration'])-float(audio['duration']))<.25,'audio_start_aligned':abs((sa['first_pts']-sv['first_pts'])-float(audio.get('start_time',0)))<.05,'writer_completed':meta['writer_status']==2,'no_stream_error':not meta['stream_error']}
result.update(checks=checks,passed=all(checks.values()),observed_capture_fps=sv['buffers']/float(v['duration']),engine_fps=None)
out=video.with_suffix('.audit.json');out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'observed_capture_fps':result['observed_capture_fps'],'audit':str(out)}));raise SystemExit(0 if result['passed'] else 1)
