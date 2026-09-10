"""Analyze in-place horse clips against constant world travel, without UE edits.
Measures horizontal support-foot residual, with both interval endpoints z<12cm.
Outputs an optional conservative Gallop distance-to-phase table.
"""
from pathlib import Path
import json,math,statistics,hashlib
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedBoss'
source=O/'horse_manifest.json';manifest=json.loads(source.read_text())
FPS=60.;WORLD_SPEED=400.;HEIGHT=12.
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'contact_definition':'Both bone-head samples below z=12 cm; no runtime IK or turn included.',
        'metric':'Sum of horizontal support-foot world displacement divided by summed contact observation time; time-weighted mean.',
        'world_speed_cm_s':WORLD_SPEED,'clips':{}}

def analyze(label):
    clip=manifest['clips'][label];ref=clip['stance_backward_speed_cm_s'];feet=clip['foot_head_positions_cm']
    count=clip['frames']-1;contacts=[];raw=[]
    for i in range(count):
        on=[{'foot':name,'vx':(p[i+1][0]-p[i][0])*FPS,'vy':(p[i+1][1]-p[i][1])*FPS}
            for name,p in feet.items() if p[i][2]<HEIGHT and p[i+1][2]<HEIGHT]
        backward=[-x['vx'] for x in on if x['vx']<0]
        raw.append(statistics.median(backward) if backward else ref);contacts.append(on)
    smooth=[.25*raw[(i-1)%count]+.5*raw[i]+.25*raw[(i+1)%count] for i in range(count)]
    conservative=[max(ref*.65,min(ref*1.35,v)) for v in smooth]
    methods={'constant_reference':[ref]*count,'raw_contact_median':raw,'smoothed_bounded_contact_median':conservative}
    out={'clip_length_s':clip['duration_seconds'],'reference_cm_s':ref,
         'ground_forward_foot_intervals':sum(x['vx']>=0 for row in contacts for x in row),
         'ground_foot_intervals':sum(len(row) for row in contacts),
         'phase_intervals_with_2_or_more_ground_feet':sum(len(row)>=2 for row in contacts),
         'methods':{}}
    for method,speeds in methods.items():
        distance=[0.];residual=observed_time=0.;instant=[]
        for speed,on in zip(speeds,contacts):
            ds=speed/FPS;dt=ds/WORLD_SPEED;distance.append(distance[-1]+ds)
            for foot in on:
                drift=math.hypot(ds+foot['vx']/FPS,foot['vy']/FPS)
                residual+=drift;observed_time+=dt;instant.append(drift/dt)
        mean=residual/observed_time
        out['methods'][method]={'time_weighted_mean_drift_at_400_cm_s':mean,
            'same_metric_at_145_cm_s':mean*145/400,'cycle_distance_cm':distance[-1],
            'cycle_world_time_at_400_s':distance[-1]/WORLD_SPEED,
            'minimum_phase_reference_cm_s':min(speeds),'maximum_phase_reference_cm_s':max(speeds),
            'maximum_anim_playrate_at_world_400':WORLD_SPEED/min(speeds),
            'phase_cumulative_distance_cm':distance}
    report['clips'][label]=out
    if label=='Gallop':
        table={'status':'Optional offline-derived experiment; actual UE foot slip and visual cadence unverified.',
            'clip_asset':'/Game/AshWell/Combat/MountedBoss/A_Horse_Gallop',
            'duration_s':clip['duration_seconds'],'sample_rate':60,
            'method':'Median backward near-ground foot velocity; airborne intervals use 477.34 cm/s; cyclic 0.25/0.5/0.25 smoothing; clamp to 0.65..1.35 of nominal.',
            'cycle_distance_cm':out['methods']['smoothed_bounded_contact_median']['cycle_distance_cm'],
            'sample_times_s':[i/FPS for i in range(count+1)],
            'cumulative_distance_cm':out['methods']['smoothed_bounded_contact_median']['phase_cumulative_distance_cm'],
            'runtime_contract':'Convert current animation time to cumulative distance by linear interpolation; add actual ground travel; wrap by cycle_distance_cm; invert the monotonic table by linear interpolation to obtain animation time. Do not additionally advance with Travel/reference speed.',
            'limits':['This does not fix incompatible simultaneous foot trajectories.','This does not correct lateral turn sliding.','This does not fix low quality contact poses or gait transitions.']}
        (O/'gallop-phase-distance-lut.json').write_text(json.dumps(table,indent=2))

for name in ['Walk','Gallop']:analyze(name)
(O/'gait-phase-distance-analysis.json').write_text(json.dumps(report,indent=2))
for name,c in report['clips'].items():
    print(name,{k:round(v['time_weighted_mean_drift_at_400_cm_s'],3) for k,v in c['methods'].items()})
