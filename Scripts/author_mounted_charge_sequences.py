"""Author editable source actions and bake FBX sequences for UE AnimBP/Montage.
No runtime procedural pose is substituted for the engine animation graph.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion

R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedChargeSample'
REPORT={}
def export(rig,name,frames):
    s=bpy.context.scene;s.frame_start=0;s.frame_end=frames-1;s.render.fps=60
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(O/f'{name}.fbx'),use_selection=True,object_types={'ARMATURE'},
        use_space_transform=False,axis_forward='X',axis_up='Z',add_leaf_bones=False,bake_anim=True,
        bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE')

def bake(rig,name,frames,pose):
    rig.animation_data_create();action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
    for frame in range(frames):
        bpy.context.scene.frame_set(frame);wanted=pose(frame/60)
        for p in rig.pose.bones:
            parent=p.parent.name if p.parent else None
            parent_rest=rest[parent] if parent else Matrix.Identity(4)
            parent_pose=wanted[parent] if parent else Matrix.Identity(4)
            p.matrix_basis=(parent_rest.inverted()@rest[p.name]).inverted()@parent_pose.inverted()@wanted[p.name]
            p.rotation_mode='QUATERNION'
            p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
    export(rig,name,frames);REPORT[name]={'duration':(frames-1)/60,'frames':frames}

def point_rotation(rest,head,tail):
    q=(rest.to_quaternion()@Vector((0,1,0))).rotation_difference((tail-head).normalized())@rest.to_quaternion()
    return Matrix.Translation(head)@q.to_matrix().to_4x4()

def limb(a,b,c,target,pole):
    upper=(b-a).length;lower=(c-b).length;d=(target-a);dist=min(d.length,upper+lower-.1);direction=d.normalized()
    bend=(pole-a)-direction*(pole-a).dot(direction);bend.normalize()
    along=(upper*upper-lower*lower+dist*dist)/(2*dist)
    knee=a+direction*along+bend*math.sqrt(max(0,upper*upper-along*along))
    return knee,a+direction*dist

bpy.ops.wm.open_mainfile(filepath=str(O/'KnightPrepared.blend'));rig=bpy.data.objects['SampleKnightRig']
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
feet={'Left':Vector((12,35,35)),'Right':Vector((12,-35,35))}
hands={'Left':Vector((35,27,114)),'Right':Vector((31,-31,108))}
def rider(t,charge=False):
    # Six authored beats remain one continuous sequence; UE owns playback and blending.
    keys=[(0,0,0),(0.75,10,-24),(1.15,20,-27),(1.65,24,-26),(2.05,22,30),(2.40,10,20),(2.95,-9,8),(3.55,0,0)]
    lean=0;twist=0
    if charge:
        for (ta,la,ya),(tb,lb,yb) in zip(keys,keys[1:]):
            if ta<=t<=tb:
                f=(t-ta)/(tb-ta);f=f*f*(3-2*f);lean=la+(lb-la)*f;twist=ya+(yb-ya)*f;break
    breathe=math.sin(t*math.pi)*.55
    pivot=rest['Hips'].translation
    torso=Matrix.Translation(pivot+Vector((0,0,breathe)))@Matrix.Rotation(math.radians(lean),4,'Y')@Matrix.Rotation(math.radians(twist),4,'Z')@Matrix.Translation(-pivot)
    wanted={n:torso@m for n,m in rest.items()}
    for side in ['Left','Right']:
        thigh=side+'UpLeg';lower=side+'Leg';foot=side+'Foot'
        a=wanted[thigh].translation;b=rest[lower].translation;c=rest[foot].translation
        knee,ankle=limb(a,b,c,feet[side],Vector((80,feet[side].y,75)))
        wanted[thigh]=point_rotation(rest[thigh],a,knee);wanted[lower]=point_rotation(rest[lower],knee,ankle)
        wanted[foot]=rest[foot].copy();wanted[foot].translation=ankle
        for n in [side+'ToeBase',side+'Toe_end']:
            parent=rig.data.bones[n].parent.name;wanted[n]=wanted[parent]@rest[parent].inverted()@rest[n]
        upper=side+'Arm';fore=side+'ForeArm';hand=side+'Hand';a=wanted[upper].translation
        target=hands[side].copy()
        if charge and side=='Right':target=torso@target+Vector((6,0,-3))
        else:target.z+=breathe*.2
        elbow,grip=limb(a,rest[fore].translation,rest[hand].translation,target,Vector((-30,85 if side=='Left' else -85,90)))
        wanted[upper]=point_rotation(rest[upper],a,elbow);wanted[fore]=point_rotation(rest[fore],elbow,grip)
        wanted[hand]=rest[hand].copy();wanted[hand].translation=grip
        if charge and side=='Right':
            prepare=min(1,t/.95);prepare=prepare*prepare*(3-2*prepare)
            sweep=max(0,min(1,(t-1.73)/.47));sweep=sweep*sweep*(3-2*sweep)
            recover=max(0,min(1,(t-2.45)/1.10));recover=recover*recover*(3-2*recover)
            yaw=math.radians(-65+110*sweep)
            idle_dir=Vector((.28,0,.96)).normalized();attack_dir=Vector((math.cos(yaw),math.sin(yaw),-.42)).normalized()
            direction=idle_dir.lerp(attack_dir,prepare*(1-recover)).normalized()
            rotation=idle_dir.rotation_difference(direction)@rest[hand].to_quaternion()
            wanted[hand]=Matrix.Translation(grip)@rotation.to_matrix().to_4x4()
        end=side+'Hand_End';wanted[end]=wanted[hand]@rest[hand].inverted()@rest[end]
    return wanted
bake(rig,'A_SampleRider_SeatedIdle',121,lambda t:rider(t))
bake(rig,'A_SampleRider_ChargeSweep',214,lambda t:rider(t,True))
rig.animation_data.action=bpy.data.actions['A_SampleRider_SeatedIdle'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderAuthored.blend'))
REPORT['rider_contacts_cm']={'left_foot':list(feet['Left']),'right_foot':list(feet['Right']),'seat_hips':list(rest['Hips'].translation)}

# Sample the existing licensed horse actions, already normalized to centimetres/+X.
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceAssets/MountedBoss/MountedHorsePrepared.blend'))
src=bpy.data.objects['MountedHorseRig'];source_rest={b.name:b.matrix_local.copy() for b in src.data.bones};samples={}
for label in ['Idle','Walk','Gallop']:
    action=bpy.data.actions['A_Horse_'+label];src.animation_data.action=action
    if action.slots:src.animation_data.action_slot=action.slots[0]
    frames=round(action.frame_range[1]-action.frame_range[0])+1
    samples[label]=[]
    for f in range(frames):
        bpy.context.scene.frame_set(f);samples[label].append({p.name:p.matrix.copy() for p in src.pose.bones})
bpy.ops.wm.open_mainfile(filepath=str(O/'HorsePrepared.blend'));rig=bpy.data.objects['SampleHorseRig']
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
mapping={'Bone_000':'Back','Bone_001':'Back','Bone_003':'Torso','Bone_002':'Torso2','Bone_016':'Torso3',
 'Bone_015':'Neck1','Bone_020':'Neck2','Bone_019':'Neck2','Bone_038':'Neck3','Bone_037':'Neck3',
 'Bone_045':'Head','Bone_044':'Head','Bone_043':'Head','Bone_042':'Head','Bone_041':'Head',
 'Bone_018':'Back','Bone_017':'Back'}
for side,nums in [('R',[51,50,49,48,47,46]),('L',[57,56,55,54,53,52])]:
    for n,srcname in zip(nums,['FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','FF','FF']):mapping[f'Bone_{n:03}']=srcname+'.'+side
for side,nums in [('R',[30,29,28,27,26,25]),('L',[36,35,34,33,32,31])]:
    for n,srcname in zip(nums,['BackLeg','BackUpperLeg','BackLowerLeg','IKBackLeg','FFB','FFB']):mapping[f'Bone_{n:03}']=srcname+'.'+side
for i,n in enumerate([14,13,12,11,10]):mapping[f'Bone_{n:03}']='Tail'+str(i+1)
for label,poses in samples.items():
    def pose_at(t):
        source=poses[min(len(poses)-1,round(t*60))];out={}
        for b in rig.data.bones:
            n=b.name;p=b.parent.name if b.parent else None
            base=out[p]@rest[p].inverted()@rest[n] if p else rest[n].copy()
            if n in mapping:
                sn=mapping[n];delta=source[sn].to_quaternion()@source_rest[sn].to_quaternion().inverted()
                q=delta@rest[n].to_quaternion();head=base.translation.copy()
                if p is None:head+=(source[sn].translation-source_rest[sn].translation)*.75
                base=Matrix.Translation(head)@q.to_matrix().to_4x4()
            out[n]=base
        return out
    bake(rig,'A_SampleHorse_'+label,len(poses),pose_at)
rig.animation_data.action=bpy.data.actions['A_SampleHorse_Idle'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'HorseRetargeted.blend'))
REPORT['horse_mapping']=mapping
(O/'animation_manifest.json').write_text(json.dumps(REPORT,indent=2))
print('SAMPLE_SEQUENCES_READY',json.dumps(REPORT))
