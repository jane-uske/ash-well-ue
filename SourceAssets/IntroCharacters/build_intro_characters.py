"""Detailed V2 workers with an original restrained procedural animation rig.

Blender 5.2; source metres, +X forward, +Y right, +Z up. No root motion.
Only reads CharactersV2 and writes IntroCharacters.
"""
from pathlib import Path
import bpy, math, json
from mathutils import Vector, Matrix, Quaternion

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'CharactersV2/build_expedition_figures.py'
FPS=30

def clamp(x):return max(0.,min(1.,x))
def smooth(x):
    x=clamp(x);return x*x*(3-2*x)
def lean(p):
    p=Vector(p);p.x+=max(0,p.z-.78)*.084;p.y+=.005*math.sin(max(0,p.z-.28)*2.8);return p

HAND_WORDS=['gloved palm','glove finger','Glove finger','Finger tip','Glove thumb','Glove soft','Glove dorsal']
HEAD_WORDS=['balaclava','helmet','Helmet','respirator','Respirator','Eye visor']
ARM_WORDS=['coat sleeve','sleeve cuff','elbow reinforcement','elbow cloth']
BOOT_WORDS=['boot','Boot','Toe cap']
COAT_WORDS=['expedition coat','coat hem','coat back seam','split-vent','Coat vertical flap']
SHOULDER_WORDS=['shoulder steel','Shoulder rolled','Shoulder rivet']

def rig_weights(obj):
    """Assign original builder parts before joining, retaining exact UVs and slots."""
    name=obj.name
    # Curves were already converted by the source builder.
    if obj.type!='MESH':return
    for v in obj.data.vertices:
        p=obj.matrix_world@v.co;sy='R' if p.y>=0 else 'L';z=p.z
        if 'Lantern' in name:
            weights={'lantern_'+('L' if CURRENT_COMPANION else 'R'):1.}
        elif any(w in name for w in HEAD_WORDS):weights={'head':1.}
        elif any(w in name for w in HAND_WORDS):weights={'hand_'+sy:1.}
        elif any(w in name for w in SHOULDER_WORDS):weights={'upperarm_'+sy:1.}
        elif any(w in name for w in ARM_WORDS):
            # Smooth transition over the actual bent elbow, not nearest-bone binding.
            lo=smooth((1.19-z)/.16)
            hand=.20*smooth((.99-z)/.055) if 'cuff' in name else 0.
            weights={'upperarm_'+sy:1-lo,'forearm_'+sy:lo-hand,'hand_'+sy:hand}
        elif any(w in name for w in BOOT_WORDS):weights={'foot_'+sy:1.}
        elif 'Trouser leg' in name or 'Knee leather' in name or 'trouser cuff' in name:
            lo=smooth((.56-z)/.14)
            weights={'thigh_'+sy:1-lo,'calf_'+sy:lo}
        elif any(w in name for w in COAT_WORDS):
            if z<.94:
                hem=smooth((.96-z)/.35)
                weights={'pelvis':1-hem,'coat_'+sy:hem}
            else:
                sp=smooth((z-1.04)/.28)
                pelvis=1-smooth((z-.94)/.17)
                weights={'pelvis':pelvis,'spine_01':(1-pelvis)*(1-sp),'spine_02':(1-pelvis)*sp}
        elif 'waist belt' in name or 'utility pouch' in name or 'Pouch flap' in name:
            weights={'pelvis':1.}
        elif 'storm collar' in name or 'scarf' in name or 'hood' in name:
            weights={'spine_02':.8,'neck':.2}
        else:weights={'spine_02':1.}
        for group,weight in weights.items():
            if weight>1e-6:
                vg=obj.vertex_groups.get(group) or obj.vertex_groups.new(name=group)
                vg.add([v.index],max(0.,weight),'REPLACE')

# Reuse the approved original modelling functions; all modifications stay here.
source=SOURCE.read_text().split("entries=[build_figure(")[0]
source=source.replace("OUT = Path(__file__).resolve().parent","OUT = Path(__file__).resolve().parent")
source=source.replace("    # Join and bake the world placement into geometry, preserving origin = world zero.",
    "    for part in PARTS:\n        rig_weights(part)\n    # Join and bake the world placement into geometry, preserving origin = world zero.")
source=source.replace("light_local=lamp(wrists[-1] if stop else wrists[1])","light_local=lamp(wrists[-1] if CURRENT_COMPANION else wrists[1])")
source=source.replace("        glove(wrist,stop and sy==1)","        before_hand=len(PARTS)\n        glove(wrist,CURRENT_COMPANION and sy==1)\n        if CURRENT_COMPANION and sy==1:\n            pivot=Vector(wrist)\n            turn=Matrix.Rotation(math.pi,4,'Y')\n            for hp in PARTS[before_hand:]:\n                hp.matrix_world=Matrix.Translation(pivot) @ turn @ Matrix.Translation(-pivot) @ hp.matrix_world")
source=source.replace("    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_custom_props=True)","    # Rigged exports are made below after adding the skeleton.")
exec(compile(source,str(SOURCE),'exec'),globals())

def rig_spec():
    d={}
    def b(name,head,tail,parent=None):d[name]=(lean(head),lean(tail),parent)
    # Root is intentionally not leaned, and stays identity through every clip.
    d['root']=(Vector((0,0,0)),Vector((0,0,.1)),None)
    b('pelvis',(0,0,.88),(0,0,1.04),'root')
    b('spine_01',(0,0,1.04),(0,0,1.29),'pelvis')
    b('spine_02',(0,0,1.29),(0,0,1.46),'spine_01')
    b('neck',(0,0,1.46),(.009,0,1.58),'spine_02')
    b('head',(.009,0,1.58),(.009,0,1.76),'neck')
    for side,sy in [('L',-1),('R',1)]:
        y=sy*.112;x=.052 if sy==1 else -.046
        b('thigh_'+side,(0,y,.88),(.07,y,.49),'pelvis')
        b('calf_'+side,(.07,y,.49),(x,y,.15),'thigh_'+side)
        b('foot_'+side,(x,y,.15),(x+.16,y,.09),'calf_'+side)
        b('upperarm_'+side,(0,sy*.222,1.411),(-.03,sy*.290,1.112),'spine_02')
        b('forearm_'+side,(-.03,sy*.290,1.112),(.052,sy*.341,.936),'upperarm_'+side)
        b('hand_'+side,(.052,sy*.341,.936),(.063,sy*.341,.860),'forearm_'+side)
        b('lantern_'+side,(.07,sy*.341,.866),(.07,sy*.341,.674),'hand_'+side)
        b('lamp_light_'+side,(.07,sy*.341,.674),(.07,sy*.341,.649),'lantern_'+side)
        b('coat_'+side,(0,sy*.10,.91),(0,sy*.15,.465),'pelvis')
    return d

SPEC=rig_spec()
def build_rig(mesh,name):
    bpy.ops.object.select_all(action='DESELECT')
    arm=bpy.data.armatures.new(name+'_Skeleton')
    rig=bpy.data.objects.new(name+'_Rig',arm);bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,tail,parent) in SPEC.items():
        bone=arm.edit_bones.new(name);bone.head=head;bone.tail=tail
        if parent:bone.parent=arm.edit_bones[parent]
        bone.use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'
    mod=mesh.modifiers.new('AshWell semantic skin','ARMATURE');mod.object=rig
    mesh.parent=rig
    return rig

def ik(a,target,l1,l2,pole):
    delta=target-a;d=max(1e-5,min(delta.length,l1+l2-.001));direction=delta.normalized()
    along=(l1*l1-l2*l2+d*d)/(2*d)
    height=math.sqrt(max(0.,l1*l1-along*along))
    perp=Vector(pole)-a;perp-=direction*perp.dot(direction)
    if perp.length<1e-6:perp=Vector((1,0,0))
    return a+direction*along+perp.normalized()*height

def set_bone(rig,name,head,tail,extra=None):
    pb=rig.pose.bones[name];rest=rig.data.bones[name]
    direction=(tail-head).normalized();rd=(rest.tail_local-rest.head_local).normalized()
    q=rd.rotation_difference(direction) @ rest.matrix_local.to_quaternion()
    if extra:q=extra@q
    pb.matrix=Matrix.LocRotScale(head,q,Vector((1,1,1)))
    bpy.context.view_layer.update()

def transformed_point(p,bob,yaw):
    q=Quaternion((0,0,1),yaw);return q@Vector(p)+Vector((0,0,bob))

def pose_frame(rig,time,mode,companion):
    phase=time*2*math.pi/1.4
    walking=1.0 if mode=='Walk' else 0.
    sign=smooth(time/1.55) if mode=='StopSignal' else (1. if mode=='SignalHold' else 0.)
    if mode=='StopSignal':walking=(1-smooth(time/.6))*.12
    bob=-.025*walking+.008*math.cos(phase*2)*walking+.002*math.sin(time*2*math.pi/2.8)*(1-walking)
    yaw=math.radians(1.2)*math.sin(phase)*walking
    body=lambda p:transformed_point(p,bob,yaw)
    root=rig.pose.bones['root'];root.matrix=rig.data.bones['root'].matrix_local.copy()
    # Torso/head stay quiet enough to preserve the mass of the worn backpack.
    for name in ['pelvis','spine_01','spine_02','neck','head']:
        h,t,_=SPEC[name];extra=None
        if name=='head':extra=Quaternion((0,0,1),math.radians(-11)*sign)
        set_bone(rig,name,body(h),body(t),extra)
    for side,sy in [('L',-1),('R',1)]:
        p=phase+(math.pi if sy<0 else 0.)
        hip=body(SPEC['thigh_'+side][0])
        footrest=SPEC['foot_'+side][0]
        # The rear half of the ellipse is the planted stance, the forward half the swing.
        foot=footrest+Vector((-.18*math.cos(p)*walking,0,.070*max(0,math.sin(p))*walking))
        l1=(SPEC['thigh_'+side][1]-SPEC['thigh_'+side][0]).length
        l2=(SPEC['calf_'+side][1]-SPEC['calf_'+side][0]).length
        knee=ik(hip,foot,l1,l2,hip+Vector((1,0,-.3)))
        set_bone(rig,'thigh_'+side,hip,knee)
        set_bone(rig,'calf_'+side,knee,foot)
        toe=foot+(SPEC['foot_'+side][1]-SPEC['foot_'+side][0])
        # Lifted foot tips slightly down, feet remain level while planted.
        toe.z-=.008*max(0,math.sin(p))*walking
        set_bone(rig,'foot_'+side,foot,toe)
        sh=body(SPEC['upperarm_'+side][0])
        wrist=body(SPEC['forearm_'+side][1])+Vector((.055*math.cos(p)*walking,0,.010*math.sin(p)*walking))
        if companion and side=='R':wrist=wrist.lerp(lean((.11,.491,1.537)),sign)
        ul=(SPEC['upperarm_'+side][1]-SPEC['upperarm_'+side][0]).length
        fl=(SPEC['forearm_'+side][1]-SPEC['forearm_'+side][0]).length
        pole=sh+Vector((-.26,sy*.1,-.3))
        if companion and side=='R':pole=pole.lerp(sh+Vector((.32,.34,-.35)),sign)
        elbow=ik(sh,wrist,ul,fl,pole)
        set_bone(rig,'upperarm_'+side,sh,elbow)
        set_bone(rig,'forearm_'+side,elbow,wrist)
        handdir=SPEC['hand_'+side][1]-SPEC['hand_'+side][0]
        if companion and side=='R':handdir=Quaternion((0,1,0),math.pi*sign)@handdir
        set_bone(rig,'hand_'+side,wrist,wrist+handdir)
        # Independent lantern hanging from the hand: very small pendular motion.
        rest_offset=SPEC['lantern_'+side][0]-SPEC['hand_'+side][0]
        lh=wrist+rest_offset
        sway=math.radians(3.2)*math.sin(phase-.6)*walking+math.radians(.35)*math.sin(phase)
        lt=lh+Quaternion((0,1,0),sway)@(SPEC['lantern_'+side][1]-SPEC['lantern_'+side][0])
        set_bone(rig,'lantern_'+side,lh,lt)
        set_bone(rig,'lamp_light_'+side,lt,lt+(lt-lh).normalized()*.025)
        ch,ct,_=SPEC['coat_'+side]
        coat_angle=math.radians(3.4)*math.cos(p-.6)*walking
        coathead=body(ch);coattail=coathead+Quaternion((0,1,0),coat_angle)@(ct-ch)
        set_bone(rig,'coat_'+side,coathead,coattail)

def new_action(rig,name,mode,duration,companion):
    rig.animation_data_create();rig.animation_data.action=None
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    end=round(duration*FPS)+1
    for frame in range(1,end+1):
        bpy.context.scene.frame_set(frame)
        pose_frame(rig,(frame-1)/FPS,mode,companion)
        for bone in rig.pose.bones:
            bone.keyframe_insert('location',frame=frame,group=bone.name)
            bone.keyframe_insert('rotation_quaternion',frame=frame,group=bone.name)
            bone.keyframe_insert('scale',frame=frame,group=bone.name)
    action['duration_seconds']=duration;action['root_motion']=False
    return action,end

def export_fbx(path,rig,mesh=None,animation=None,end=1):
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    if mesh:mesh.select_set(True)
    bpy.context.view_layer.objects.active=rig
    rig.animation_data_create();rig.animation_data.action=animation
    bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=end;bpy.context.scene.frame_set(1)
    if animation is None:
        for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','ARMATURE'},
        use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,
        bake_anim=animation is not None,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,
        axis_forward='-Y',axis_up='Z',global_scale=1.,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',use_custom_props=True,
        armature_nodetype='NULL',primary_bone_axis='Y',secondary_bone_axis='X')

bpy.context.scene.render.fps=FPS
entries=[]
for role in ['Protagonist','Companion']:
    CURRENT_COMPANION=role=='Companion'
    name='SK_Intro_'+role
    info=build_figure(name,[0,0,0],0,False)
    char_mesh=bpy.data.objects[name]
    rig=build_rig(char_mesh,name)
    for obj in bpy.context.scene.objects:
        obj.hide_render=obj not in [char_mesh,rig]
    clips=[]
    modes=[('Walk',1.4),('Idle',2.8)]
    if CURRENT_COMPANION:modes += [('StopSignal',3.0),('SignalHold',2.8)]
    for mode,duration in modes:
        action,end=new_action(rig,'A_Intro_'+role+'_'+mode,mode,duration,CURRENT_COMPANION)
        export_fbx(OUT/(action.name+'.fbx'),rig,animation=action,end=end)
        clips.append({'name':action.name,'file':action.name+'.fbx','duration_seconds':duration,
            'frames':[1,end],'fps':FPS,'loop':mode in ['Walk','Idle','SignalHold'],'root_motion':False})
    export_fbx(OUT/(name+'.fbx'),rig,mesh=char_mesh)
    info.update({'skeletal_mesh':name+'.fbx','rig':rig.name,'animations':clips,
        'root_origin_m':[0,0,0],'height_m':info['bounds_m'][1][2]-info['bounds_m'][0][2],
        'capsule_radius_cm':34,'capsule_half_height_cm':90,
        'lantern_bone':'lantern_L' if CURRENT_COMPANION else 'lantern_R',
        'lantern_light_bone':'lamp_light_L' if CURRENT_COMPANION else 'lamp_light_R',
        'lantern_light_bone_offset_m':[0,0,0],
        'lantern_light_note':'Attach the point light directly to lamp_light_L/R at zero offset; this bone is at the glass centre.',
        'walk_cycle_seconds':1.4,'nominal_walk_speed_cm_s':51.4})
    entries.append(info)

bpy.context.scene.render.fps=FPS
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'IntroCharacters.blend'))
manifest={'version':1,'source':'Original CharactersV2 procedural geometry with original semantic skinning and animation',
 'source_coordinates':'Metres, +X forward, +Y right, +Z up. Feet/root centred at world origin.',
 'fbx':{'axis_forward':'-Y','axis_up':'Z','units':'metres','apply_scale_options':'FBX_SCALE_UNITS',
    'bone_primary_axis':'Y','bone_secondary_axis':'X','add_leaf_bones':False},
 'bones':list(SPEC),'assets':entries,
 'limitations':['Procedural prototype animation, no motion capture or cloth simulation.',
  'Closed long coat uses two secondary bones; extreme poses are outside its intended range.',
  'All clips in place; translate character actor at the documented walking speed.',
  'StopSignal begins from neutral feet and should be blended in over 0.2 seconds when possible.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print('INTRO_CHARACTERS_READY '+json.dumps(manifest,ensure_ascii=False))
