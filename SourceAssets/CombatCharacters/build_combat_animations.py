"""Original procedural combat clips for the existing Intro protagonist skeleton.

Run with Blender in background. Only writes this directory. Metres, +X forward.
"""
from pathlib import Path
import bpy, math, json, hashlib
from mathutils import Vector, Matrix, Quaternion

OUT = Path(__file__).resolve().parent
INTRO = OUT.parent / 'IntroCharacters'
FPS = 60
bpy.ops.wm.open_mainfile(filepath=str(INTRO / 'IntroCharacters.blend'))
rig = bpy.data.objects['SK_Intro_Protagonist_Rig']
mesh = bpy.data.objects['SK_Intro_Protagonist']
# The original builder's final second-character mesh cleanup applied the first
# character's modifier in its .blend preview. FBX skin weights are intact; restore
# the preview modifier here so source QA evaluates the very same weighted mesh.
if not any(m.type=='ARMATURE' and m.object==rig for m in mesh.modifiers):
    preview_skin=mesh.modifiers.new('Combat preview skin','ARMATURE');preview_skin.object=rig
scene = bpy.context.scene
scene.render.fps = FPS
SPEC = {b.name: (b.head_local.copy(), b.tail_local.copy(), b.parent.name if b.parent else None) for b in rig.data.bones}

def smooth(x):
    x = max(0., min(1., x))
    return x*x*(3.-2.*x)

def key_sample(keys, time):
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if time <= tb:
            f = smooth((time-ta)/(tb-ta))
            if isinstance(va, (tuple, list, Vector)):
                return Vector(va).lerp(Vector(vb), f)
            return va+(vb-va)*f
    return Vector(keys[-1][1]) if isinstance(keys[-1][1], (tuple, list, Vector)) else keys[-1][1]

def set_bone(name, head, tail, extra=None):
    pb = rig.pose.bones[name]
    rest = rig.data.bones[name]
    q = (rest.tail_local-rest.head_local).normalized().rotation_difference((tail-head).normalized()) @ rest.matrix_local.to_quaternion()
    if extra: q = extra @ q
    pb.matrix = Matrix.LocRotScale(head, q, Vector((1,1,1)))
    bpy.context.view_layer.update()

def solve_limb(a, target, first, second, pole):
    l1 = (SPEC[first][1]-SPEC[first][0]).length
    l2 = (SPEC[second][1]-SPEC[second][0]).length
    delta = target-a
    direction = delta.normalized()
    d = max(.01, min(delta.length, l1+l2-.002))
    target = a+direction*d
    along = (l1*l1-l2*l2+d*d)/(2*d)
    height = math.sqrt(max(0., l1*l1-along*along))
    perp = pole-a
    perp -= direction*perp.dot(direction)
    if perp.length < 1e-5: perp = Vector((1,0,0))
    mid = a+direction*along+perp.normalized()*height
    set_bone(first,a,mid)
    set_bone(second,mid,target)
    return target

def pose(time, mode):
    bob=0.; pitch=0.; yaw=0.; offset=Vector((0,0,0)); dodge=0.; death=0.
    if mode=='Attack':
        yaw=math.radians(key_sample([(0,0),(.18,-18),(.30,-27),(.45,25),(.56,32),(.8333333,0)],time))
        pitch=math.radians(key_sample([(0,0),(.30,-7),(.43,15),(.57,12),(.8333333,0)],time))
        bob=key_sample([(0,0),(.30,-.04),(.43,-.085),(.60,-.04),(.8333333,0)],time)
    elif mode=='Dodge':
        dodge=key_sample([(0,0),(.10,.80),(.20,1),(.34,1),(.50,.25),(.5833333,0)],time)
        bob=-.31*dodge; pitch=math.radians(48)*dodge
    elif mode=='Hit':
        impact=key_sample([(0,0),(.08,1),(.18,.75),(.45,0)],time)
        pitch=math.radians(-19)*impact; bob=-.04*impact; offset.x=-.055*impact
    elif mode=='Death':
        death=key_sample([(0,0),(.18,.12),(.55,.60),(.92,1),(1.3,1)],time)
        pitch=math.radians(-87)*death
        bob=-.53*death; offset.x=-.08*death
    elif mode=='CombatWalk':
        phase=time*2*math.pi/.60
        bob=-.105+.014*math.cos(phase*2)
        pitch=math.radians(8); yaw=math.radians(3)*math.sin(phase)
    offset.z += bob
    pivot=SPEC['pelvis'][0]
    rotation=Quaternion((0,0,1),yaw) @ Quaternion((0,1,0),pitch)
    body=lambda p: pivot+rotation@(Vector(p)-pivot)+offset
    rig.pose.bones['root'].matrix=rig.data.bones['root'].matrix_local.copy()
    for name in ['pelvis','spine_01','spine_02','neck','head']:
        set_bone(name, body(SPEC[name][0]), body(SPEC[name][1]))
    for side, sy in [('L',-1),('R',1)]:
        foot=SPEC['foot_'+side][0].copy()
        foot_tail=SPEC['foot_'+side][1]-foot
        phase=time*2*math.pi/.60+(math.pi if side=='L' else 0.)
        if mode=='CombatWalk':
            q=((time/.60)+(.5 if side=='L' else 0.))%1.
            if q < .5:
                foot.x += .36-1.44*q
            else:
                swing=(q-.5)*2
                foot.x += -.36+.72*smooth(swing)
                foot.z += .15*math.sin(math.pi*swing)
                foot_tail=Quaternion((0,1,0),math.radians(12)*math.sin(math.pi*swing))@foot_tail
        elif mode=='Dodge':
            foot.x += (-.09 if side=='L' else .09)*dodge
            foot.y += sy*.08*dodge
        elif mode=='Attack':
            foot.y += sy*.04*math.sin(math.pi*min(1,time/.8333333))
        elif mode=='Death':
            airborne=smooth((death-.25)/.65)
            foot=foot.lerp(body(foot)+Vector((0,sy*.08*death,0)),airborne)
            foot_tail=Quaternion((0,1,0),pitch*airborne)@foot_tail
        hip=body(SPEC['thigh_'+side][0])
        pole=hip+rotation@Vector((1,0,-.15))
        foot=solve_limb(hip,foot,'thigh_'+side,'calf_'+side,pole)
        set_bone('foot_'+side,foot,foot+foot_tail)
        shoulder=body(SPEC['upperarm_'+side][0])
        wrist=body(SPEC['forearm_'+side][1])
        handdir=rotation@(SPEC['hand_'+side][1]-SPEC['hand_'+side][0])
        if mode=='Attack' and side=='L':
            # Shoulder-length-constrained diagonal hammer arc: high rear preparation,
            # fast downstroke, weight through the torso, deliberate recovery.
            target=key_sample([(0,tuple(SPEC['forearm_L'][1])),(.14,(-.10,-.47,1.30)),
                              (.30,(-.10,-.48,1.66)),(.37,(.23,-.38,1.45)),
                              (.45,(.42,-.22,1.08)),(.56,(.20,-.07,.95)),
                              (.8333333,tuple(SPEC['forearm_L'][1]))],time)
            wrist=target+Vector((0,0,bob*.25))
            angle=math.radians(key_sample([(0,0),(.30,-85),(.45,25),(.56,35),(.8333333,0)],time))
            handdir=Quaternion((0,1,0),angle)@(SPEC['hand_L'][1]-SPEC['hand_L'][0])
        elif mode=='Dodge':
            wrist=wrist.lerp(body((.25,sy*.32,1.22)),dodge)
        elif mode=='CombatWalk':
            wrist += Vector((.14*math.cos(phase),0,.018*math.sin(phase)))
        elif mode=='Hit':
            wrist.y += sy*.09*impact
        elif mode=='Death':
            wrist += Vector((.08*death,sy*.12*death,.025*death))
        elbow_pole=shoulder+rotation@Vector((-.20,sy*.22,-.24))
        if mode=='Attack' and side=='L':elbow_pole=shoulder+Vector((-.22,-.65,.04))
        wrist=solve_limb(shoulder,wrist,'upperarm_'+side,'forearm_'+side,elbow_pole)
        set_bone('hand_'+side,wrist,wrist+handdir)
        # Lantern stays gravitationally vertical except for the final fall.
        lamp_offset=SPEC['lantern_'+side][0]-SPEC['hand_'+side][0]
        lamphead=wrist+lamp_offset
        sway=math.radians(6)*math.sin(phase-.4) if mode=='CombatWalk' else math.radians(5)*math.sin(time*9)
        lamp_rot=Quaternion((0,1,0),sway+pitch*death)
        lamptail=lamphead+lamp_rot@(SPEC['lantern_'+side][1]-SPEC['lantern_'+side][0])
        set_bone('lantern_'+side,lamphead,lamptail)
        set_bone('lamp_light_'+side,lamptail,lamptail+(lamptail-lamphead).normalized()*.025)
        coat_head=body(SPEC['coat_'+side][0])
        coat_dir=SPEC['coat_'+side][1]-SPEC['coat_'+side][0]
        if mode=='CombatWalk':coat_rot=Quaternion((0,1,0),math.radians(-14)*math.cos(phase-.25))
        elif mode=='Dodge':coat_rot=Quaternion((0,1,0),math.radians(-53)*dodge)
        else:coat_rot=rotation
        set_bone('coat_'+side,coat_head,coat_head+coat_rot@coat_dir)

clips=[]
for mode,duration in [('Attack',50/60),('Dodge',35/60),('Hit',27/60),('Death',78/60),('CombatWalk',36/60)]:
    name='A_Combat_Protagonist_'+mode
    rig.animation_data_create();rig.animation_data.action=None
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    end=round(duration*FPS)+1
    for frame in range(1,end+1):
        scene.frame_set(frame);pose((frame-1)/FPS,mode)
        for b in rig.pose.bones:
            b.keyframe_insert('location',frame=frame,group=b.name)
            b.keyframe_insert('rotation_quaternion',frame=frame,group=b.name)
            b.keyframe_insert('scale',frame=frame,group=b.name)
    action['duration_seconds']=duration;action['root_motion']=False
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    scene.frame_start=1;scene.frame_end=end;scene.frame_set(1)
    path=OUT/(name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE'},
        add_leaf_bones=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,
        axis_forward='-Y',axis_up='Z',global_scale=1.,apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',use_custom_props=True,
        armature_nodetype='NULL',primary_bone_axis='Y',secondary_bone_axis='X')
    clips.append({'name':name,'file':path.name,'duration_seconds':duration,'fps':FPS,'frames':[1,end],
                  'root_motion':False,'loop':mode=='CombatWalk','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest={'source':'Original procedural combat animation on the unchanged Intro protagonist rig',
          'skeleton':'/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton',
          'coordinates':'Metres, +X forward, +Y right, +Z up; FBX -Y forward / Z up',
          'bones':list(SPEC),'animations':clips,
          'attack_windows_seconds':{'windup':[0,.30],'active':[.30,.45],'recovery':[.45,50/60]},
          'combat_walk_nominal_cm_s':240,'combat_walk_step_interval_seconds':.30,
          'combat_walk_step_distance_cm':72,'left_weapon_bone':'hand_L','lantern_light_bone':'lamp_light_R',
          'limitations':['Procedural prototype poses, not motion capture.',
                         'Dodge is a compact low step with actor translation supplied by runtime; no full roll.',
                         'Left hand weapon is a separate runtime attachment; this package contains animation only.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['A_Combat_Protagonist_Attack']
scene.frame_set(19)
for obj in scene.objects:
    if obj.type=='MESH':obj.hide_render=obj!=mesh
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CombatAnimations.blend'))
print('COMBAT_ANIMATIONS_EXPORTED '+json.dumps(clips))
