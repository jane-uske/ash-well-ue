"""Author editable source actions and bake FBX sequences for UE AnimBP/Montage.
No runtime procedural pose is substituted for the engine animation graph.
"""
import bpy,json,math,os
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion

R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedChargeSample'
BASE=O;ASSEMBLY_SCALE=float(os.environ.get('ASHWELL_ASSEMBLY_SCALE','1'));HORSE_SCALE=1.3*ASSEMBLY_SCALE
O=R/'SourceAssets/MountedReferenceProduction'/('AssemblyRevision' if ASSEMBLY_SCALE!=1 else 'Animation');O.mkdir(parents=True,exist_ok=True)
REPORT={'assembly_scale':ASSEMBLY_SCALE,'horse_world_scale':HORSE_SCALE}
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

bpy.ops.wm.open_mainfile(filepath=str(BASE/'KnightPrepared.blend'))
rig=bpy.data.objects['SampleKnightRig'];rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
feet={'Left':Vector((12,35,35)),'Right':Vector((12,-35,35))}

# Editable source beats, remapped below onto the inspected reference interval. Cubic tangents carry momentum through intermediate keys;
# the sole attack timing authority remains the existing UE Montage / Notify State.
# t, forward lean, chest yaw, right grip xyz, pelvis settle
BEATS=[
 (0,0,0,31,-31,108,0),
 (.40,2,-8,5,-40,134,-.2),
 (.95,8,-22,-5,-42,140,-1.0),
 (1.15,12,-28,-4,-43,137,-1.6),
 (1.58,24,-32,10,-43,132,-1.3),
 (1.73,28,-27,29,-38,111,-1.2),
 (1.94,22,9,43,-25,108,-.4),
 (2.20,15,30,38,-12,130,.3),
 (2.45,7,26,28,-18,139,.6),
 (2.85,-6,15,24,-23,130,1.0),
 (3.20,-3,4,29,-28,113,.4),
 (3.55,0,0,31,-31,108,0),
]
# Source BV1cw411M7xw: raised shoulder load (20.45 s), low pass
# (21.04 s), rising follow-through (21.40 s). These are authored 3D
# interpretations of visible poses, not extracted original-game rotations.
# Unwrapped yaw preserves the circular path through the shoulder load.
BLADE_BEATS=[(0,0,73.74),(.40,110,50),(.95,135,12),(1.15,140,10),
             (1.50,155,8),(1.62,215,-12),(1.73,295,-23),
             (1.94,345,-20),(2.10,380,18),(2.20,395,35),
             (2.45,400,45),(2.85,375,62),(3.20,360,73.74),(3.55,360,73.74)]
def curve(t,keys=BEATS):
    for i,(a,b) in enumerate(zip(keys,keys[1:])):
        if a[0]<=t<=b[0]:
            f=(t-a[0])/(b[0]-a[0]);duration=b[0]-a[0]
            prev=keys[max(0,i-1)];nxt=keys[min(len(keys)-1,i+2)]
            ma=[0 if i==0 else (b[k]-prev[k])/(b[0]-prev[0])*duration for k in range(1,len(a))]
            mb=[0 if i+2==len(keys) else (nxt[k]-a[k])/(nxt[0]-a[0])*duration for k in range(1,len(a))]
            return [(2*f**3-3*f*f+1)*a[k]+(f**3-2*f*f+f)*ma[k-1]+(-2*f**3+3*f*f)*b[k]+(f**3-f*f)*mb[k-1] for k in range(1,len(a))]
    return list(keys[-1][1:])
def rotate_at(matrix,lean,yaw):
    pivot=matrix.translation.copy()
    return Matrix.Translation(pivot)@Matrix.Rotation(math.radians(yaw),4,'Z')@Matrix.Rotation(math.radians(lean),4,'Y')@Matrix.Translation(-pivot)@matrix

def pose(t,charge):
    lean,yaw,hx,hy,hz,settle=curve(t) if charge else (0,0,31,-31,108,0)
    breathe=math.sin(t*math.pi)*.35
    wanted={}
    # Small pelvic motion preserves saddle contact; lumbar/chest carry the larger action.
    split={'Hips':(.12,.16),'Spine02':(.32,.27),'Spine01':(.33,.28),'Spine':(.23,.29),
           'neck':(-.30,-.24),'Head':(-.15,-.12)}
    for b in rig.data.bones:
        parent=b.parent.name if b.parent else None
        m=wanted[parent]@rest[parent].inverted()@rest[b.name] if parent else rest[b.name].copy()
        if not parent:m.translation+=Vector((0,0,settle+breathe))
        if b.name in split:
            l,y=split[b.name];m=rotate_at(m,lean*l,yaw*y)
        wanted[b.name]=m
    for side in ['Left','Right']:
        thigh,lower,foot=(side+x for x in ['UpLeg','Leg','Foot'])
        a=wanted[thigh].translation
        # Preserve true rest segment lengths regardless of root movement.
        b=a+(rest[lower].translation-rest[thigh].translation)
        c=b+(rest[foot].translation-rest[lower].translation)
        knee,ankle=limb(a,b,c,feet[side],Vector((80,feet[side].y,75)))
        wanted[thigh]=point_rotation(rest[thigh],a,knee);wanted[lower]=point_rotation(rest[lower],knee,ankle)
        wanted[foot]=rest[foot].copy();wanted[foot].translation=ankle
        for n in [side+'ToeBase',side+'Toe_end']:
            parent=rig.data.bones[n].parent.name;wanted[n]=wanted[parent]@rest[parent].inverted()@rest[n]
        upper,fore,hand=(side+x for x in ['Arm','ForeArm','Hand'])
        a=wanted[upper].translation
        target=Vector((hx,hy,hz)) if side=='Right' else Vector((29+lean*.15,30,113+breathe*.2))
        b=a+(rest[fore].translation-rest[upper].translation)
        c=b+(rest[hand].translation-rest[fore].translation)
        pole_height=103 if side=='Left' else max(103,hz-7)
        elbow,grip=limb(a,b,c,target,Vector((-22,72 if side=='Left' else -72,pole_height)))
        wanted[upper]=point_rotation(rest[upper],a,elbow);wanted[fore]=point_rotation(rest[fore],elbow,grip)
        wanted[hand]=rest[hand].copy();wanted[hand].translation=grip
        if charge and side=='Right':
            angle,elevation=map(math.radians,curve(t,BLADE_BEATS))
            idle=Vector((.28,0,.96)).normalized()
            direction=Vector((math.cos(angle)*math.cos(elevation),math.sin(angle)*math.cos(elevation),math.sin(elevation)))
            wanted[hand]=Matrix.Translation(grip)@(idle.rotation_difference(direction)@rest[hand].to_quaternion()).to_matrix().to_4x4()
        end=side+'Hand_End';wanted[end]=wanted[hand]@rest[hand].inverted()@rest[end]
    return wanted


# Preserve the prior visible pose work, retime its authored keys to the reference.
TIME_MAP=[(0,0),(.40,.32),(.95,.75),(1.15,.9),(1.58,1.35),(1.73,1.48),
          (1.94,1.75),(2.10,1.98),(2.20,2.18),(2.45,2.7),(2.85,3.85),(3.20,4.65),(3.55,5.8)]
def mapped(t):
    for (a,x),(b,y) in zip(TIME_MAP,TIME_MAP[1:]):
        if a<=t<=b:return x+(y-x)*(t-a)/(b-a)
    return 5.8
BEATS=[(mapped(k[0]),*k[1:]) for k in BEATS]
BLADE_BEATS=[(mapped(k[0]),*k[1:]) for k in BLADE_BEATS]
bake(rig,'A_ReferenceRider_SeatedIdle',121,lambda t:pose(t,False))
bake(rig,'A_ReferenceRider_ChargeSweep',349,lambda t:pose(t,True))
rig.animation_data.action=bpy.data.actions['A_ReferenceRider_ChargeSweep'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderAuthored.blend'))
REPORT['rider_beats']=BEATS;REPORT['blade_beats']=BLADE_BEATS
# The rider remains a separate skeletal actor; release the stirrup IK at death.
BEATS=[(0,0,0,31,-31,108,0),(.45,10,-5,28,-32,102,-2),(1.2,37,-14,22,-30,87,-5),(2.0,45,-18,16,-28,81,-7),(2.8,45,-18,16,-28,81,-7)]
BLADE_BEATS=[(0,0,73.74),(.6,15,55),(1.5,25,10),(2.8,25,10)]
bake(rig,'A_ReferenceRider_Death',169,lambda t:pose(t,True))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderDeathAuthored.blend'))


# Sample the existing UE-retargeted gait clips, retaining the target rest skeleton.
# Native UE Foot Placement / Leg IK handles runtime ground contact after the Slot.
timing=json.loads((O.parent/'charge-timing.json').read_text())
source_info=json.loads((O.parent/'HorseSource/export.json').read_text())
cache={}
for label in ['Idle','Walk','Gallop']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(O.parent/'HorseSource'/(label+'.fbx')))
    src=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    action=src.animation_data.action;start,end=action.frame_range
    samples=[];count=round(source_info[label]['seconds']*60)
    for f in range(count+1):
        frame=start+(end-start)*f/count;bpy.context.scene.frame_set(int(frame),subframe=frame%1)
        samples.append({p.name:p.matrix_basis.copy() for p in src.pose.bones})
    cache[label]=samples
bpy.ops.wm.open_mainfile(filepath=str(BASE/'HorsePrepared.blend'))
rig=bpy.data.objects['SampleHorseRig'];rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
for p in rig.pose.bones:
    for c in list(p.constraints):p.constraints.remove(c)
def blend_matrix(a,b,f):
    at,ar,asc=a.decompose();bt,br,bsc=b.decompose()
    return Matrix.LocRotScale(at.lerp(bt,f),ar.slerp(br,f),asc.lerp(bsc,f))
def clip_pose(label,phase):
    arr=cache[label];f=(phase%1)*(len(arr)-1);i=int(f);n=min(i+1,len(arr)-1)
    return {k:blend_matrix(arr[i][k],arr[n][k],f-i) for k in arr[i]}
walk_phase=gallop_phase=0.;horse_poses=[];last_distance=0
for f,(t,distance) in enumerate(timing['distance_samples_cm']):
    travel=distance-last_distance;last_distance=distance
    walk_phase+=travel/(140.25174*1.1666667*ASSEMBLY_SCALE);gallop_phase+=travel/(562.19050*.6*ASSEMBLY_SCALE)
    speed=(travel*60 if f else timing['speed_keys_cm_s'][0][1])/ASSEMBLY_SCALE
    walk=clip_pose('Walk',walk_phase);gallop=clip_pose('Gallop',gallop_phase);idle=clip_pose('Idle',t/3.3333333)
    running=max(0,min(1,(speed-180)/290));moving=max(0,min(1,speed/100))
    local={k:blend_matrix(idle[k],blend_matrix(walk[k],gallop[k],running),moving) for k in idle}
    # The body compresses into braking, then releases into the standing pose.
    brake=math.exp(-((t-3.9)/.38)**2)
    acceleration=math.exp(-((t-1.15)/.38)**2)
    wanted={}
    for b in rig.data.bones:
        parent=b.parent.name if b.parent else None
        m=(wanted[parent]@rest[parent].inverted()@rest[b.name] if parent else rest[b.name])@local[b.name]
        if not parent:
            m.translation+=Vector((-3*brake,0,-4.5*brake))
            m=rotate_at(m,-5*brake+2*acceleration,0)
        wanted[b.name]=m
    horse_poses.append(wanted)
bake(rig,'A_ReferenceHorse_ChargeSweep',349,lambda t:horse_poses[min(348,round(t*60))])
# Enforce support intervals using Blender's native IK solver before UE import.
# The reference root displacement stays in the actor; stance targets travel back
# through component space by exactly that distance. Runtime slope correction is UE.
raw_action=rig.animation_data.action;raw_action.name='A_ReferenceHorse_RawGaitBlend'
foot_names=['Bone_053','Bone_047','Bone_032','Bone_026'];ik_parents=['Bone_054','Bone_048','Bone_033','Bone_027']
source_positions={n:[p[n].translation.copy() for p in horse_poses] for n in foot_names}
contacts={}
for n,points in source_positions.items():
    contacts[n]=[p.z<8. for p in points]
targets={};constraints=[];rotation_constraints=[]
for n,parent in zip(foot_names,ik_parents):
    empty=bpy.data.objects.new('SupportTarget_'+n,None);bpy.context.collection.objects.link(empty);targets[n]=empty
    constraint=rig.pose.bones[parent].constraints.new('IK');constraint.name='Native support placement';constraint.target=empty;constraint.chain_count=4;constraint.use_tail=True;constraint.use_stretch=False;constraint.iterations=128
    constraints.append((rig.pose.bones[parent],constraint))
    rotation=rig.pose.bones[n].constraints.new('COPY_ROTATION');rotation.name='Native sole orientation';rotation.target=empty;rotation.target_space='WORLD';rotation.owner_space='WORLD';rotation_constraints.append((rig.pose.bones[n],rotation))
anchors={};evaluated=[];previous={};drift_before=drift_after=contact_dt=0.
for frame,(t,distance) in enumerate(timing['distance_samples_cm']):
    bpy.context.scene.frame_set(frame)
    for n,(pb,constraint) in zip(foot_names,constraints):
        is_contact=contacts[n][frame];point=source_positions[n][frame]
        root_offset=Vector((distance/HORSE_SCALE,0,0))
        if is_contact and (frame==0 or not contacts[n][frame-1]):
            anchors[n]=point+root_offset;anchors[n].z=max(anchors[n].z,5.)
        # Short release blend avoids a velocity discontinuity at lift-off.
        weight=1.
        constraint.influence=weight
        target=(anchors.get(n,point+root_offset)-root_offset) if is_contact else point.copy()
        if not is_contact:
            nearest=min([abs(i-frame) for i in range(max(0,frame-4),min(349,frame+5)) if contacts[n][i]] or [4])
            blend=min(1.,nearest/4);blend=blend*blend*(3-2*blend)
            target.z=max(target.z,5.+7.*blend)
        targets[n].location=target
        source_rotation=horse_poses[frame][n].to_quaternion();plant_rotation=rest[n].to_quaternion()
        if is_contact:
            age=next((frame-i for i in range(frame-1,max(-1,frame-4),-1) if not contacts[n][i]),4)
            rotation_weight=min(1.,age/2)
        else:rotation_weight=1.-blend
        targets[n].rotation_mode='QUATERNION';targets[n].rotation_quaternion=source_rotation.slerp(plant_rotation,rotation_weight)
        targets[n].keyframe_insert('rotation_quaternion',frame=frame)
        targets[n].keyframe_insert('location',frame=frame);constraint.keyframe_insert('influence',frame=frame)
    bpy.context.view_layer.update();wanted={p.name:p.matrix.copy() for p in rig.pose.bones};evaluated.append(wanted)
    for n in foot_names:
        before=source_positions[n][frame]*HORSE_SCALE+Vector((distance,0,0));after=wanted[n].translation*HORSE_SCALE+Vector((distance,0,0))
        if frame and contacts[n][frame] and contacts[n][frame-1] and frame<270:
            drift_before+=(before-previous[n][0]).xy.length;drift_after+=(after-previous[n][1]).xy.length;contact_dt+=1/60
        previous[n]=(before,after)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'HorseContactAuthoring.blend'))
for pb,constraint in constraints+rotation_constraints:pb.constraints.remove(constraint)
bake(rig,'A_ReferenceHorse_ChargeSweep',349,lambda t:evaluated[min(348,round(t*60))])
REPORT['offline_native_ik']={'before_support_drift_cm_s':drift_before/contact_dt,'after_support_drift_cm_s':drift_after/contact_dt,'contact_seconds':contact_dt,'solver':'Blender native IK, four links; runtime remains UE Foot Placement / Leg IK'}
rig.animation_data.action=bpy.data.actions['A_ReferenceHorse_ChargeSweep'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'HorseAuthored.blend'))
REPORT['horse_source']='Existing UE-retargeted Idle/Walk/Gallop, distance-driven cadence; authored brake compression. No merged skeleton.'
REPORT['scope']='A/B animation candidate, not accepted. Contact details occluded in the original are authored interpretations.'
(O/'animation_manifest.json').write_text(json.dumps(REPORT,indent=2));print('REFERENCE_ANIMATION_READY',json.dumps(REPORT))
