"""Original, deterministic short combat foley, 48 kHz mono PCM16."""
import math, random, struct, wave, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets/CombatAudio'
OUT.mkdir(parents=True,exist_ok=True)
SR=48000
report=[]
for index,(name,duration) in enumerate([('Swing',.48),('Impact',.55),('Dodge',.58)]):
    rng=random.Random(20260905+index)
    values=[];last=0.0
    for i in range(int(SR*duration)):
        t=i/SR;u=t/duration
        noise=rng.uniform(-1,1);filtered=noise-last*.75;last=noise
        if name=='Impact':
            envelope=(1-math.exp(-t*1800))*math.exp(-t*12)
            v=envelope*(.48*filtered+.28*math.sin(2*math.pi*113*t)+.14*math.sin(2*math.pi*727*t)+.08*math.sin(2*math.pi*1483*t))
        elif name=='Swing':
            envelope=math.sin(math.pi*u)**2.8
            v=envelope*(filtered*.32+.09*math.sin(2*math.pi*(190*t-95*t*t)))
        else:
            envelope=math.sin(math.pi*u)**1.5
            v=envelope*filtered*.22+.06*math.sin(2*math.pi*620*t)*math.exp(-t*13)
        values.append(v*min(1,t/.003,(duration-t)/.012))
    peak=max(map(abs,values));scale=.77/max(peak,.001)
    data=b''.join(struct.pack('<h',round(v*scale*32767)) for v in values)
    path=OUT/f'AW_Combat_{name}.wav'
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(data)
    report.append({'file':path.name,'duration':duration,'sample_rate':SR,'peak':.77,'origin':'original deterministic synthesis'})
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
