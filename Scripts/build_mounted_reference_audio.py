"""Prepare licensed Foley derivatives. Original archives/recordings are immutable."""
from pathlib import Path
import array,hashlib,json,math,subprocess
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedReferenceProduction/Audio';P=O/'Originals';D=O/'Prepared';D.mkdir(exist_ok=True)
SR=48000
def decode(path):
    out=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar',str(SR),'-f','f32le','-'])
    a=array.array('f');a.frombytes(out);return a
def hits(path,count=3):
    a=decode(path);block=240;power=[max(abs(x) for x in a[i:i+block]) for i in range(0,len(a),block)]
    threshold=max(power)*.2;starts=[];last=-1000
    for i,v in enumerate(power):
        if v>threshold and i-last>SR/block*.25:starts.append(max(0,(i*block)/SR-.015))
        if v>threshold:last=i
    return starts[:count]
manifest={'license':'CC0-1.0','original_game_audio':False,'sources':[
 {'author':'Ben Jaszczak & Brian Nelson / Still North Media','url':'https://opengameart.org/content/medieval-sound-effects-weapon-impacts'},
 {'author':'Ben Jaszczak & Brian Nelson / Still North Media','url':'https://opengameart.org/content/medieval-sound-effects-weapon-textures'},
 {'author':'StarNinjas','url':'https://opengameart.org/comment/92361'},
 {'author':'Kenney','url':'https://kenney.nl/assets/impact-sounds'}],
 'processing':'48 kHz mono, selected transients, trim/short fade, layered recorded impacts; no original-game extraction','files':[],'cues':{}}
def render(name,layers):
    mixed=array.array('f',[0.]*(SR*3))
    provenance=[]
    for path,start,duration,gain,rate in layers:
        a=decode(path);begin=int(start*SR);end=min(len(a),begin+int(duration*SR));a=a[begin:end]
        peak=max((abs(x) for x in a),default=0)
        if not peak:raise ValueError(path)
        for i in range(min(len(mixed),int(len(a)/rate))):
            f=i*rate;j=int(f);frac=f-j
            v=(a[j]*(1-frac)+a[min(j+1,len(a)-1)]*frac)*gain/peak
            fade=min(1.,i/96,max(0.,(len(a)/rate-i)/960))
            mixed[i]+=v*fade
        provenance.append({'file':str(path.relative_to(O)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'start':start,'duration':duration,'gain':gain,'rate':rate})
    n=next((i+1 for i in range(len(mixed)-1,-1,-1) if abs(mixed[i])>.0001),1);mixed=mixed[:n]
    peak=max(abs(x) for x in mixed);gain=.70/max(peak,.0001)
    mixed=array.array('f',(v*gain for v in mixed));dest=D/(name+'.wav')
    subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-c:a','pcm_s16le',str(dest)],input=mixed.tobytes(),check=True)
    manifest['files'].append({'name':name,'layers':provenance,'seconds':n/SR,'peak_dbfs':20*math.log10(max(abs(x) for x in mixed)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
K=P/'KenneyImpact/Audio';S=P/'sword_-_starninjas_1/sword - StarNinjas';C=P/'sword_clash_-_starninjas_0'
metal=P/'StillNorthImpacts/Axe Norse Sword Blade on Blade.wav'
axe=P/'StillNorthTextures/Axe Swing.wav'
metal_starts=hits(metal,4);axe_starts=hits(axe,4)
assert len(metal_starts)>=4 and len(axe_starts)>=4
for i in range(3):
    def k(n):return K/(n+f'_{i:03}.ogg')
    choices={
     'PlayerSwing':[(S/f'sword.{i+1}.ogg',0,.7,1,1)],
     'HalberdSwing':[(axe,axe_starts[i],.7,1,.8)],
     'ArmourHit':[(metal,metal_starts[i],min(.75,metal_starts[i+1]-metal_starts[i]-.03),1,.94),(k('impactPunch_heavy'),0,.5,.4,.88)],
     'WeaponHit':[(C/f'sword_clash.{i+1}.ogg',0,.6,.65,.88),(k('impactPunch_heavy'),0,.6,1,.85)],
     'ShieldBlock':[(metal,metal_starts[i],min(.65,metal_starts[i+1]-metal_starts[i]-.03),.6,.82),(k('impactPlate_heavy'),0,.7,1,.8)],
     'BodyHit':[(k('impactPunch_heavy'),0,.7,1,.73),(k('impactSoft_heavy'),0,.6,.7,.9)],
     'Landing':[(k('impactSoft_heavy'),0,.8,1,.65),(k('impactMining'),0,.8,.45,.8)],
     'Hoof':[(k('footstep_concrete'),0,.45,1,.84),(k('footstep_grass'),0,.4,.7,.9)]}
    for group,layers in choices.items():
        name=f'AW_Mounted_{group}_{i+1:02}';render(name,layers)
        manifest['cues'].setdefault('SC_'+group,[]).append(name)
manifest['archives']=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in P.iterdir() if p.suffix in ['.7z','.zip']]
(O/'audio-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'LICENSES.md').write_text('# Mounted combat audio\n\nAll source collections are CC0 1.0; no purchases or original Elden Ring audio. Source URLs, authors, segment times, transformations and hashes are in audio-manifest.json. Kenney original license: Originals/KenneyImpact/License.txt. Original archives remain preserved.\n')
print(json.dumps({'waves':len(manifest['files']),'cues':list(manifest['cues'])}))
