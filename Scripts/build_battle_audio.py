"""Original deterministic short industrial combat effects; no external samples."""
from pathlib import Path
import math,random,wave,struct,json
O=Path(__file__).resolve().parents[1]/'SourceAssets/BattlePolish';O.mkdir(parents=True,exist_ok=True)
rate=48000;rng=random.Random(7008);manifest=[]
for name,duration in [('MetalHit',.65),('GroundSlam',1.3),('Swing',.42),('Roll',.58),('Kick',.4),('Drag',.65),('Windup',.8)]:
 values=[];low=0
 for i in range(round(rate*duration)):
  t=i/rate;n=rng.uniform(-1,1);low=.88*low+.12*n
  if name in ['MetalHit','GroundSlam','Kick']:
   heavy=name=='GroundSlam';e=math.exp(-t*(5 if heavy else 12));metal=sum(math.sin(math.tau*f*t)*math.exp(-t*d) for f,d in [(431,12),(719,17),(1133,22)])/3
   v=(.5*math.sin(math.tau*(52*t+1.6*(1-math.exp(-18*t))))+.3*low+.2*metal)*e + .18*n*math.exp(-t*65)
  elif name=='Swing':v=(n-low)*math.sin(math.pi*t/duration)**2*.55+low*.15
  elif name=='Roll':v=low*.7*math.sin(math.pi*t/duration)**.7+(n-low)*.13*math.exp(-((t-.39)/.055)**2)
  elif name=='Drag':v=(low*.8+.25*math.sin(math.tau*907*t))*min(1,t/.025)*min(1,(duration-t)/.12)*(.55+.45*math.sin(math.tau*31*t)**2)
  else:v=(math.sin(math.tau*(110*t+48*t*t))*.25+low*.3)*math.sin(math.pi*t/duration)**.6
  v*=min(1,t/.002)*min(1,(duration-t)/.015);values.append(v)
 peak=max(abs(x) for x in values);gain=.92/max(.001,peak)
 path=O/f'AW_Battle_{name}.wav'
 with wave.open(str(path),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(struct.pack('<'+'h'*len(values),*(round(max(-1,min(1,v*gain))*32767) for v in values)))
 rms=(sum((v*gain)**2 for v in values)/len(values))**.5
 manifest.append({'file':path.name,'seconds':duration,'rms_dbfs':20*math.log10(rms),'source':'Original deterministic synthesis; no third-party samples'})
(O/'audio-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(manifest)
