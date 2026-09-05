"""Validate actual serialized PCM files, loop seams, and reference-mix loudness."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import wave
import numpy as np

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
checks=[]
for a in manifest['assets']:
    path=root/a['file']
    with wave.open(str(path),'rb') as f:
        channels=f.getnchannels(); sample_rate=f.getframerate(); width=f.getsampwidth(); n=f.getnframes()
        x=np.frombuffer(f.readframes(n),dtype='<i2').astype(np.float64).reshape(-1,channels)/32768
    problems=[]
    if (sample_rate,width,channels)!=(48000,2,a['channels']): problems.append('invalid header')
    if abs(n/sample_rate-a['duration_seconds'])>.0001: problems.append('duration mismatch')
    if not np.all(np.isfinite(x)): problems.append('non-finite PCM')
    if np.max(np.abs(x))>=.999: problems.append('clipping')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=a['sha256']: problems.append('hash mismatch')
    seam=None
    if a['looping']:
        internal=np.max(np.abs(np.diff(x,axis=0)),axis=1)
        boundary=float(np.max(np.abs(x[0]-x[-1])))
        seam={'boundary_delta':boundary,'internal_delta_99th_percentile':float(np.quantile(internal,.99)),
              'boundary_percentile':float(np.mean(internal<=boundary)*100)}
        if boundary>np.quantile(internal,.999): problems.append('loop boundary discontinuity exceeds ordinary adjacent-sample movement')
    checks.append({'id':a['id'],'passed':not problems,'issues':problems,'loop_seam':seam})

cmd=['/opt/homebrew/bin/ffmpeg','-hide_banner','-i',str(root/'AW_Intro30s_AudioPreview.wav'),
     '-filter_complex','ebur128=peak=true','-f','null','-']
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
summary=r.stderr.rsplit('Summary:',1)[-1]
stats={
    'integrated_lufs':float(re.search(r'I:\s*(-?[\d.]+) LUFS',summary).group(1)),
    'loudness_range_lu':float(re.search(r'LRA:\s*([\d.]+) LU',summary).group(1)),
    'true_peak_dbfs':float(re.search(r'Peak:\s*(-?[\d.]+) dBFS',summary).group(1)),
    'method':'ffmpeg ebur128=peak=true on the serialized 30 s stereo PCM preview'
}
report={'passed':all(c['passed'] for c in checks) and r.returncode==0,
        'scope':'Serialized audio headers, checksums, clipping, loop seams and measured reference-mix loudness. This is not a listening evaluation.',
        'files_checked':len(checks),'checks':checks,'preview_loudness':stats}
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'files_checked':len(checks),'preview_loudness':stats,
                  'loops':[c for c in checks if c['loop_seam']]},indent=2))
assert report['passed']
