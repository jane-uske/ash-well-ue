"""Bake the licensed Quaternius horse into an independent centimetre UE rig.
All constraints are evaluated from the original clips, then baked at 60 fps.
Run in disposable background Blender; does not edit the downloaded original.
"""
import bpy, json, math, statistics, hashlib
from pathlib import Path
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets/MountedBoss'
SRC=OUT/'originals/Horse_Quaternius.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC))
s=bpy.context.scene
source=bpy.data.objects['AnimalArmature']
horse=bpy.data.objects['Horse']
for track in source.animation_data.nla_tracks: track.mute=True
source.animation_data.action=None
for p in source.pose.bones: p.matrix_basis=Matrix.Identity(4)
s.frame_set(0)
ROT=Matrix.Rotation(math.pi/2,4,'Z')  # original -Y becomes +X
SCALE=47.0
FLOOR=-min(v.co.z for v in horse.data.vertices)*SCALE
def converted_matrix(m):
    d=ROT@m
    d.translation=d.translation*SCALE+Vector((0,0,FLOOR))
    return d

names=[b.name for b in source.data.bones]
rest={b.name:converted_matrix(b.matrix_local) for b in source.data.bones}
clip_sources={
    'Idle':'Idle','Walk':'Walk','Gallop':'Gallop','Death':'Death',
    'Kick':'Attack_Kick','Headbutt':'Attack_Headbutt',
    'Jump':'Jump_toIdle','GallopJump':'Gallop_Jump',
    'HitLeft':'Idle_HitReact_Left','HitRight':'Idle_HitReact_Right',
}
sampled={}
for label, srcname in clip_sources.items():
    a=bpy.data.actions[srcname]
    source.animation_data.action=a
    if a.slots: source.animation_data.action_slot=a.slots[0]
    first,last=a.frame_range
    count=round((last-first)*2)
    frames=[]
    for i in range(count+1):
        f=first+i*.5
        s.frame_set(math.floor(f),subframe=f%1)
        frames.append({p.name:converted_matrix(p.matrix.copy()) for p in source.pose.bones})
    sampled[label]=frames

source.animation_data.action=None
for p in source.pose.bones:p.matrix_basis=Matrix.Identity(4)
s.frame_set(0)
arm=bpy.data.armatures.new('MountedHorseSkeleton')
rig=bpy.data.objects.new('MountedHorseRig',arm)
s.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
root=arm.edit_bones.new('root');root.head=(0,0,0);root.tail=(0,0,10)
for b in source.data.bones:
    n=arm.edit_bones.new(b.name)
    n.length=b.length*SCALE
    n.matrix=rest[b.name]
for b in source.data.bones:
    arm.edit_bones[b.name].parent=arm.edit_bones[b.parent.name] if b.parent else root
bpy.ops.object.mode_set(mode='OBJECT')
for p in rig.pose.bones:p.rotation_mode='QUATERNION'

mesh=horse.copy();mesh.data=horse.data.copy();mesh.name='SK_Horse'
s.collection.objects.link(mesh)
mesh.parent=rig;mesh.matrix_basis=Matrix.Identity(4);mesh.matrix_parent_inverse=Matrix.Identity(4)
normalizer=Matrix.Translation((0,0,FLOOR))@ROT@Matrix.Scale(SCALE,4)
mesh.data.transform(normalizer)
for mod in mesh.modifiers:
    if mod.type=='ARMATURE':mod.object=rig
for p in mesh.data.polygons:p.use_smooth=True
for ob in [horse,source]:bpy.data.objects.remove(ob,do_unlink=True)
s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01;s.render.fps=60

def export(name,objects,anim=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(OUT/f'{name}.fbx'),use_selection=True,
        object_types={'MESH','ARMATURE'},use_space_transform=False,
        axis_forward='X',axis_up='Z',add_leaf_bones=False,
        bake_anim=anim,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,
        bake_anim_simplify_factor=0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',
        mesh_smooth_type='FACE')
export('SK_Horse',[mesh,rig])
report={
    'source_url':'https://quaternius.com/packs/ultimateanimatedanimals.html',
    'source_drive_id':'1XEstRdaMvbc7Xb5tK_mk6KP6fkFz_WXh',
    'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
    'license':'CC0; originals/License.txt','cost':0,
    'status':'Low polygon movement validation asset; not realistic final art',
    'units':'centimetres, bone/component scale one, +X forward, feet z=0',
    'fbx_import':'convert_scene=False, convert_scene_unit=False, import_uniform_scale=1',
    'scale_from_source':SCALE,'ground_offset_cm':FLOOR,
    'rest_bones':{b.name:{'head_cm':list(b.head_local),'tail_cm':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in arm.bones},
    'body_anchor':'Torso2','saddle_world_rest_cm':[0,0,175],
    'foot_bones':['FF.L','FF.R','FFB.L','FFB.R'],
    'clips':{},'materials':{},
    'missing':['Dedicated rear/stomp clip','Dedicated stop/turn clips','Synchronized rider performance clips'],
}

for label,frames in sampled.items():
    rig.animation_data_create()
    action=bpy.data.actions.new('A_Horse_'+label)
    action.use_fake_user=True
    rig.animation_data.action=action
    for i,poses in enumerate(frames):
        s.frame_set(i)
        for name in names:
            p=rig.pose.bones[name]
            parent=p.bone.parent.name
            parent_rest=rest[parent] if parent in rest else Matrix.Identity(4)
            parent_pose=poses[parent] if parent in poses else Matrix.Identity(4)
            local_rest=parent_rest.inverted()@rest[name]
            local_pose=parent_pose.inverted()@poses[name]
            # Solve local channels from known desired parent matrices. Setting
            # p.matrix successively uses stale evaluated parent transforms.
            p.matrix_basis=local_rest.inverted()@local_pose
            p.keyframe_insert('location',frame=i)
            p.keyframe_insert('rotation_quaternion',frame=i)
            p.keyframe_insert('scale',frame=i)
    s.frame_start=0;s.frame_end=len(frames)-1;s.frame_set(0)
    export('A_Horse_'+label,[rig],True)
    duration=(len(frames)-1)/60
    feet={name:[list(frame[name].translation) for frame in frames] for name in report['foot_bones']}
    velocities=[]
    for points in feet.values():
        low=min(p[2] for p in points)
        for a,b in zip(points,points[1:]):
            velocity=-(b[0]-a[0])*60
            if a[2]<low+5 and b[2]<low+5 and velocity>10:
                velocities.append(velocity)
    reference=statistics.median(velocities) if velocities else 0
    report['clips'][label]={
        'source_clip':clip_sources[label],'duration_seconds':duration,
        'sample_rate':60,'frames':len(frames),'root_motion':False,
        'stance_backward_speed_cm_s':reference,
        'estimated_stride_cm':reference*duration,
        'support_velocity_samples':len(velocities),
        'foot_head_positions_cm':feet,
    }

rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
s.frame_set(0)
for m in mesh.data.materials:
    report['materials'][m.name]={'base_color':list(m.diffuse_color),'roughness':.69,'metallic':0}
bpy.context.view_layer.update()
report['mesh_bounds_cm']=[[min((mesh.matrix_world@Vector(c))[i] for c in mesh.bound_box) for i in range(3)],
                          [max((mesh.matrix_world@Vector(c))[i] for c in mesh.bound_box) for i in range(3)]]
report['vertices']=len(mesh.data.vertices)
(OUT/'horse_manifest.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MountedHorsePrepared.blend'))
print('MOUNTED_HORSE_READY',json.dumps({k:{x:v for x,v in c.items() if x!='foot_head_positions_cm'} for k,c in report['clips'].items()}))
