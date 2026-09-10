"""Original industrial stems and local Apache-licensed Kokoro voice; no paid API.
Run using uv with kokoro, misaki[zh], numpy, soundfile.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'SourceAssets/PolishAudio';OUT.mkdir(parents=True,exist_ok=True)
sr=48000;t=np.arange(sr*16)/sr;rng=np.random.default_rng(7007)
noise=rng.normal(0,1,len(t));smoothed=np.convolve(noise,np.ones(65)/65,mode='same')
base=.09*np.sin(2*np.pi*41.25*t)+.025*np.sin(2*np.pi*61.875*t+.12*np.sin(2*np.pi*t/16))
stems={'Ambient':base*(.70+.3*np.sin(np.pi*t/16)**2)+.018*smoothed}
pulse=np.mod(t,1.5);beat=np.exp(-pulse*9)*np.sin(2*np.pi*(58*pulse+9*(1-np.exp(-pulse*18))))
metal=np.exp(-pulse*17)*(.027*np.sin(2*np.pi*823*t)+.023*np.sin(2*np.pi*1171*t))
stems['Combat']=.25*beat+metal+.015*np.sin(2*np.pi*82.5*t)*(1+np.sin(2*np.pi*t/8))
p=np.mod(t,.75);stems['Overload']=.1*np.exp(-p*13)*np.sin(2*np.pi*70*p)+.012*np.sin(2*np.pi*123.75*t)+.04*smoothed*np.exp(-p*6)
report=[]
for name,v in stems.items():
 v*=np.minimum(1,np.minimum(t/.025,(16-t)/.025))
 path=OUT/f'AW_Polish_{name}.wav';sf.write(path,v,sr,subtype='PCM_16')
 report.append({'file':path.name,'seconds':16,'origin':'Original deterministic synthesis','loop':True})
from kokoro import KPipeline
pipe=KPipeline(lang_code='z',device='cpu',repo_id='hexgrad/Kokoro-82M')
chunks=[]
for text in ['别。','再送电了。']:
 audio=np.concatenate([a.numpy() for _,_,a in pipe(text,voice='zm_yunxi',speed=.80)])
 chunks.extend([audio,np.zeros(12000,dtype=np.float32)])
v=np.concatenate(chunks);vt=np.arange(len(v))/24000
# Keep words legible under a restrained damaged-speaker coloration.
v=.82*v+.12*v*np.sin(2*np.pi*39*vt)
for delay,gain in [(.095,.16),(.21,.075)]:
 n=int(delay*24000);v[n:]+=gain*v[:-n].copy()
v*=.75/max(.001,float(np.abs(v).max()))
path=OUT/'AW_Polish_Voice.wav';sf.write(path,v,24000,subtype='PCM_16')
report.append({'file':path.name,'seconds':len(v)/24000,'origin':'Local Kokoro-82M, Apache-2.0 model; stock zm_yunxi voice; no voice clone','text':'别……再送电了。','loop':False})
for item in report:item['sha256']=hashlib.sha256((OUT/item['file']).read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
