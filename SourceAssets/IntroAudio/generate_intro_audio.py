"""Original deterministic procedural Foley for Ash Well. No sampled third-party media.

Run with NumPy; output 48 kHz PCM16 WAVs and an objective QC manifest.
Dry point-source Foley is deliberately short; add the cave through Unreal reverb.
"""
from pathlib import Path
import hashlib
import json
import math
import wave
import numpy as np

ROOT = Path(__file__).resolve().parent
SR = 48000
RNG = np.random.default_rng(20260905)
ASSETS = []


def db(x):
    return round(float(20 * np.log10(max(float(x), 1e-12))), 3)


def noise(n, low=30, high=8000, slope=0.0, rng=None):
    """Band-shaped, periodic noise. Real FFT maintains a coherent loop boundary."""
    rng = RNG if rng is None else rng
    f = np.fft.rfftfreq(n, 1 / SR)
    spec = rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))
    weights = np.maximum(f, max(low, 1)) ** slope
    weights *= 1 / np.sqrt(1 + (low / np.maximum(f, 1e-6)) ** 12)
    weights *= 1 / np.sqrt(1 + (np.maximum(f, 1e-6) / high) ** 12)
    weights[0] = 0
    y = np.fft.irfft(spec * weights, n=n)
    return y / max(np.std(y), 1e-8)


def envelope(t, attack, release, offset=0):
    q = np.maximum(t - offset, 0)
    return (1 - np.exp(-q / attack)) * np.exp(-q / release) * (t >= offset)


def fade(x, start=.008, end=.035):
    x = x.copy()
    a, b = int(start * SR), int(end * SR)
    if a:
        shape = np.linspace(0, 1, a) ** 2
        x[:a] *= shape[:, None] if x.ndim == 2 else shape
    if b:
        shape = np.linspace(1, 0, b) ** 2
        x[-b:] *= shape[:, None] if x.ndim == 2 else shape
    return x


def write(name, x, *, purpose, looping=False, peak_db=-10, rms_db=None, gain=1,
          notes='', suggested_volume=1):
    x = np.asarray(x, dtype=np.float64)
    x -= x.mean(axis=0)
    if rms_db is not None:
        x *= 10 ** (rms_db / 20) / max(np.sqrt(np.mean(x*x)), 1e-10)
    if rms_db is None or np.max(np.abs(x)) > 10 ** (peak_db/20):
        x *= 10 ** (peak_db/20) / max(np.max(np.abs(x)), 1e-10)
    x *= gain
    pcm = np.round(np.clip(x, -1, 1) * 32767).astype('<i2')
    dest = ROOT / (name + '.wav')
    with wave.open(str(dest), 'wb') as w:
        w.setnchannels(1 if x.ndim == 1 else x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    result = {
        'id': name, 'file': dest.name, 'purpose': purpose,
        'format': 'PCM16', 'sample_rate': SR, 'channels': 1 if x.ndim == 1 else x.shape[1],
        'duration_seconds': round(len(x) / SR, 4), 'looping': looping,
        'peak_dbfs': db(np.max(np.abs(x))), 'rms_dbfs': db(np.sqrt(np.mean(x*x))),
        'dc_offset': [round(float(v), 9) for v in np.atleast_1d(x.mean(axis=0))],
        'clipped_samples': int(np.count_nonzero(np.abs(pcm.astype(np.int32)) >= 32767)),
        'loop_boundary_delta_dbfs': db(np.max(np.abs(x[0] - x[-1]))) if looping else None,
        'suggested_ue_volume': suggested_volume, 'notes': notes,
        'bytes': dest.stat().st_size, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
        'provenance': 'Original procedural synthesis; generator source included. No third-party samples.'
    }
    ASSETS.append(result)
    return x


def ambience():
    duration = 24
    n = int(SR * duration)
    t = np.arange(n) / SR
    # Periodic random fields and integer-cycle modulation make both loops seamless.
    core = noise(n, 27, 170, -.6)
    body = noise(n, 75, 430, -.35)
    cycle = .79 + .12 * np.sin(2*np.pi*t/duration+.7) + .045*np.sin(6*np.pi*t/duration+1.4)
    # Quiet detuned resonances suggest structure under load, without an audible note.
    resonance = sum(a*np.sin(2*np.pi*(round(f*duration)/duration)*t+p)
                    for f,a,p in [(37.5,.08,.5),(51.4,.04,1.3),(73.1,.035,2.1),(113.7,.018,.2)])
    common = cycle * (.82*core + .16*body + resonance)
    stereo = np.column_stack([common + .06*noise(n,110,680,-.8),
                              common + .06*noise(n,110,680,-.8)])
    machine = write('AW_Amb_MachineryLoop', stereo, purpose='Deep continuous machinery heard through the well structure',
                    looping=True, rms_db=-29, peak_db=-14, suggested_volume=.85,
                    notes='24 s exact periodic loop; low fundamental is deliberately restrained. Stereo non-spatial bed, or collapse to mono for one distant source.')
    airy = noise(n, 230, 4700, -.75)
    modulation = .8 + .12*np.sin(2*np.pi*t/duration+2.4) + .06*np.sin(4*np.pi*t/duration)
    air = np.column_stack([airy*.72 + .40*noise(n,380,5800,-.6),
                           airy*.72 + .40*noise(n,380,5800,-.6)]) * modulation[:,None]
    air = write('AW_Amb_WellAirLoop', air, purpose='Restrained spacious air and distant ventilation', looping=True,
                rms_db=-36, peak_db=-22, suggested_volume=.65,
                notes='24 s exact periodic loop, no baked reverb; pairs below the machinery bed. Avoid raising it until it sounds like surf.')
    return machine, air


def footstep(index):
    # A low sole impact, heel/forefoot separation, short grit skid and scattered wet flecks.
    duration = .74 + .018*index
    t = np.arange(int(SR*duration))/SR
    n = len(t)
    impact = (.8*noise(n,45,430,-.15) + .15*noise(n,160,1250,-.2)) * envelope(t,.002,.037+.0015*index)
    delayed = .045 + .003*index
    landing = .32*noise(n,100,1650,-.35)*envelope(t,.003,.052,delayed)
    grit = .10*noise(n,550,4600,.1)*envelope(t,.012,.087,.025)
    # Sparse granular pulses, not a continuous splash or gunshot transient.
    wet = np.zeros(n)
    for j in range(14):
        onset = RNG.uniform(.015,.19)
        width = RNG.uniform(.0008,.004)
        pulse = np.exp(-((t-onset)/width)**2)
        wet += RNG.uniform(.009,.026)*noise(n,1250,6900,.05)*pulse
    stone = np.zeros(n)
    for freq, amp, decay in [(126+index*4,.055,.043),(247-index*5,.026,.029),(588+index*9,.007,.018)]:
        stone += amp*np.sin(2*np.pi*freq*t + .1)*envelope(t,.001,decay)
    x = fade(impact+landing+grit+wet+stone, .002, .055)
    return write(f'AW_Foley_WetStoneStep_{index+1:02d}', x, purpose='Heavy boot on damp cracked stone; close dry point source',
                 peak_db=-10-index%3*.7, suggested_volume=.80,
                 notes='Play one variation per actual footfall. Randomize pitch narrowly 0.96–1.04 and volume 0.85–1.0; add UE cave reflections, not another dry simultaneous footstep.')


def gear(index):
    duration = 1.35+.18*index
    t = np.arange(int(SR*duration))/SR
    n = len(t)
    x = .09*noise(n,170,1550,-.3)*envelope(t,.025,.14)
    # Sticking hinge under a changing small load: noisy friction, several inharmonic modes.
    grip = (.50+.32*np.sin(2*np.pi*(7.3+.2*index)*t+.2)**3)**2
    friction = .13*noise(n,400,2700,-.1)*grip*envelope(t,.02,.25)
    for freq,amp,release in [(173,.038,.14),(371,.019,.12),(647,.014,.17),(1021,.008,.08)]:
        freq *= 1+index*.047
        phase = 2*np.pi*(freq*t + 1.8*np.sin(2*np.pi*1.7*t))
        x += amp*np.sin(phase)*envelope(t,.02,release)
    for at,amp in [(.055,.06),(.17,.042),(.34,.026)]:
        q=np.maximum(t-at,0)
        tick= sum(np.sin(2*np.pi*f*q)*np.exp(-q/(.055+.011*j)) for j,f in enumerate([911+index*41,1473,2317]))
        x += amp*tick*envelope(t,.0006,.025,at)
    x=fade(x+friction,.007,.09)
    return write(f'AW_Foley_LanternGear_{index+1:02d}',x,purpose='Quiet lantern handle and pack fittings shifting under load',
                 peak_db=-17-index, suggested_volume=.55,
                 notes='Use sparingly every 3–5 steps, or once as the companion stops. Not a continuous rattle loop.')


def breath():
    t=np.arange(int(SR*1.1))/SR
    # A soft unvoiced exhalation; no speech/person/voice model is used.
    env=envelope(t,.045,.14,.045)
    x=(.65*noise(len(t),430,3400,-.3)+.18*noise(len(t),170,730,-.4))*env
    return write('AW_Foley_HushedBreath',fade(x,.015,.13),purpose='Brief unvoiced breath on the companion stopping beat',
                 peak_db=-23,suggested_volume=.45,
                 notes='Optional synthesized breath, not intelligible speech. Keep quiet; do not label it a voiced shush.')


def distant_structure():
    duration=5.5
    t=np.arange(int(SR*duration))/SR
    n=len(t)
    x=.70*noise(n,35,150,-.5)*envelope(t,.22,.75,.13)
    x+=.23*noise(n,110,550,-.4)*envelope(t,.07,.38,.08)
    # Nonmusical long inharmonic response of a large steel/civil structure.
    for f,a,decay in [(46.3,.13,1.4),(69.7,.07,1.1),(102.8,.05,.8),(181.4,.022,.55)]:
        x+=a*np.sin(2*np.pi*f*t)*envelope(t,.08,decay,.09)
    x=fade(x,.03,.5)
    return write('AW_Event_DistantLoadShift',x,purpose='A distant load transfers through immense machinery; triggers the companion stop',
                 peak_db=-17, suggested_volume=.9,
                 notes='Low non-explosive structural response. Spatialize 25–60 m ahead and below; allow a long dark cave reverb tail. Do not add a jump-scare rise.')


def preview(machine,air,steps,gears,exhale,load):
    mix=np.zeros((30*SR,2))
    for sound,gain in [(machine,.85),(air,.65)]:
        mix += np.tile(sound,(2,1))[:len(mix)]*gain
    schedule=[]
    def add(x,at,gain,pan=0):
        start=int(at*SR)
        if x.ndim==1:
            # Gentle equal-power pan; preview contains restrained illustrative early echoes only.
            a=(pan+1)*np.pi/4
            stereo=np.column_stack([x*np.cos(a),x*np.sin(a)])
        else: stereo=x
        end=min(len(mix),start+len(stereo))
        mix[start:end] += stereo[:end-start]*gain
        for delay,level in [(.19,.12),(.43,.07),(.73,.03)]:
            si=start+int(delay*SR);ei=min(len(mix),si+len(stereo))
            if ei>si: mix[si:ei] += stereo[:ei-si,::-1]*gain*level
    for i,at in enumerate(np.arange(1.5,14.1,.84)):
        add(steps[i%6],at,.74, -.10 if i%2 else .10)
        schedule.append({'time':round(float(at),3),'asset':f'AW_Foley_WetStoneStep_{i%6+1:02d}','role':'player footfall'})
        if i%4==1: add(gears[i%3],at+.16,.25,-.12)
    # The companion walks slightly ahead. Its faint sound avoids sounding like a doubled player.
    for i,at in enumerate(np.arange(1.1,13.8,.86)):
        add(steps[(i+2)%6],at,.18,.24)
    add(load,13.9,.83,.35)
    add(gears[1],14.45,.5,.2)
    add(exhale,14.95,.9,.20)
    schedule.extend([
        {'time':13.9,'asset':'AW_Event_DistantLoadShift','role':'distant structural cue'},
        {'time':14.45,'asset':'AW_Foley_LanternGear_02','role':'companion stops; pack settles'},
        {'time':14.95,'asset':'AW_Foley_HushedBreath','role':'optional quiet exhale'},
        {'time':15.2,'asset':None,'role':'no more footsteps; listen to the machinery through the rest of the 30 s'}
    ])
    # The demonstrator is a reference for the runtime mixer, not another layer to play in UE.
    out=write('AW_Intro30s_AudioPreview',fade(mix,1.4,2.0),purpose='30 s illustrative sound-only mix for review; DO NOT layer with runtime assets',
              peak_db=-6,suggested_volume=1,notes='Offline demonstration with light early echoes. Not imported by default. Timing is illustrative; actual footsteps must follow runtime movement.')
    return schedule


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    machine,air=ambience()
    steps=[footstep(i) for i in range(6)]
    gears=[gear(i) for i in range(3)]
    exhale=breath()
    load=distant_structure()
    timing=preview(machine,air,steps,gears,exhale,load)
    manifest={
        'version':1,'sample_rate':SR,'format':'PCM16 WAV','seed':20260905,
        'provenance':'Original procedural synthesis created for this project; no third-party samples, recordings, AI voice services, or paid assets.',
        'generator':'generate_intro_audio.py','license_note':'Original project assets; no external attribution requirement. This statement does not assign a third-party license.',
        'validation_note':'Files and signal metrics verified programmatically. No claim of human listening or perceptual loudness certification.',
        'assets':ASSETS,'timing_suggestions':timing,
        'unreal':{'import_folder':'/Game/AshWell/Audio/Intro','default_reverb':'Use one dark cave reverb/AudioVolume for point sources; dry sources are provided.',
                  'ambient':'Two non-spatial continuous stereo beds. Enable looping on their SoundWave or sound cue.',
                  'steps':'Mono; trigger from travelled distance, choose variation, attenuate companion substantially.',
                  'event':'Mono point source 25–60 m ahead and below; one event near the stop moment.',
                  'excluded_by_default':['AW_Intro30s_AudioPreview']}}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    assert all(a['clipped_samples']==0 and a['peak_dbfs']<=-6 for a in ASSETS)
    for a in ASSETS: print(a['id'],a['duration_seconds'],a['peak_dbfs'],a['rms_dbfs'],a['loop_boundary_delta_dbfs'])
    print('READY:',len(ASSETS),'assets;',sum(a['bytes'] for a in ASSETS),'bytes')


if __name__=='__main__': main()
