"""Read-only target-hoof trajectory audit in the authored Blender actions."""
import bpy,json,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceAssets/MountedChargeSample/HorseRetargeted.blend'))
rig=bpy.data.objects['SampleHorseRig'];result={}
for name in ['Idle','Walk','Gallop']:
    action=bpy.data.actions['A_SampleHorse_'+name];rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    feet={n:[] for n in ['Bone_046','Bone_052','Bone_025','Bone_031']}
    for frame in range(round(action.frame_range[1])+1):
        bpy.context.scene.frame_set(frame)
        for n in feet:feet[n].append(rig.pose.bones[n].matrix.translation.copy()*1.3)
    clip={};reference=[]
    for n,points in feet.items():
        ground=min(p.z for p in points);speeds=[]
        for a,b in zip(points,points[1:]):
            speed=-(b.x-a.x)*60
            if max(a.z,b.z)<ground+3 and speed>20:speeds.append(speed)
        clip[n]={'min_z_cm':ground,'max_z_cm':max(p.z for p in points),'stride_x_range_cm':max(p.x for p in points)-min(p.x for p in points),'low_backwards_samples':len(speeds),'median_support_speed_cm_s':statistics.median(speeds) if speeds else None}
        reference+=speeds
    result[name]={'duration':action.frame_range[1]/60,'hooves':clip,'median_support_speed_cm_s':statistics.median(reference) if reference else None}
(R/'Saved/MountedChargeStandard/gait-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
