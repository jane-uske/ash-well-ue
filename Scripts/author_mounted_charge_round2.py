"""Author editable source actions and bake FBX sequences for UE AnimBP/Montage.
No runtime procedural pose is substituted for the engine animation graph.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion

R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedChargeSample'
BASE=O;O=O/'Round2';O.mkdir(parents=True,exist_ok=True)
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

bpy.ops.wm.open_mainfile(filepath=str(BASE/'KnightPrepared.blend'))
rig=bpy.data.objects['SampleKnightRig'];rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
feet={'Left':Vector((12,35,35)),'Right':Vector((12,-35,35))}

# Editable source beats. Cubic tangents carry momentum through intermediate keys;
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

bake(rig,'A_SampleRider_SeatedIdle',121,lambda t:pose(t,False))
bake(rig,'A_SampleRider_ChargeSweep',214,lambda t:pose(t,True))
rig.animation_data.action=bpy.data.actions['A_SampleRider_ChargeSweep'];bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderAuthored.blend'))
REPORT['source_beats']=BEATS
REPORT['blade_beats_yaw_elevation']=BLADE_BEATS
REPORT['reference']='BV1cw411M7xw 19.3-25.1 s; raised load / low sweep / high release. Authored interpretation; occluded motion remains uncertain.'
REPORT['scope']='Rider only. Original Meshy exports, horse source clips and combat phase times untouched. Visual candidate, not acceptance.'
(O/'animation_manifest.json').write_text(json.dumps(REPORT,indent=2))
print('ROUND2_RIDER_READY',json.dumps(REPORT))
