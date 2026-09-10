"""CC0 Quaternius locomotion retargeted to the existing player. Run through Blender MCP."""
from pathlib import Path
import bpy, math, json
from mathutils import Matrix, Vector, Quaternion
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/SwordPass';O.mkdir(exist_ok=True)
s=bpy.context.scene;src=bpy.data.objects['Rig'];rig=bpy.data.objects['SK_Intro_Protagonist_Rig']
for obj in [src,rig]:
 obj.animation_data_create();obj.animation_data.action=None
 for tr in obj.animation_data.nla_tracks:tr.mute=True
 for b in obj.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
C=Matrix(((0,-1,0),(1,0,0),(0,0,1)));Ci=C.inverted()
mp={'pelvis':'DEF-hips','spine_01':'DEF-spine.002','spine_02':'DEF-spine.003','neck':'DEF-neck','head':'DEF-head'}
for side,ss in [('L','R'),('R','L')]:
 for t,f in [('upperarm','upper_arm'),('forearm','forearm'),('hand','hand'),('thigh','thigh'),('calf','shin'),('foot','foot')]:mp[t+'_'+side]='DEF-'+f+'.'+ss
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
base={n:src.data.bones[v].matrix_local.copy() for n,v in mp.items()}
# Retain source twist while calibrating its T-pose onto the old relaxed-arm bind pose.
cal={}
for n,v in mp.items():
 b=rig.data.bones[n];sb=src.data.bones[v]
 aim=(b.tail_local-b.head_local).normalized().rotation_difference((C@(sb.tail_local-sb.head_local)).normalized())
 cal[n]=aim.to_matrix()@rest[n].to_3x3()
def sample(action,frame):
 src.animation_data.action=bpy.data.actions[action];src.animation_data.action_slot=src.animation_data.action.slots[0]
 s.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 return {n:src.pose.bones[v].matrix.copy() for n,v in mp.items()}
guard=sample('Sword_Idle',0)
# In-place source loops, free Standard edition. Combat layers hold the sword-ready upper body.
spec=[('Idle','Idle_Loop',2.5,False),('Walk','Walk_Loop',1.333333,False),('Run','Jog_Fwd_Loop',.933333,False),('Sprint','Sprint_Loop',.666667,False),('Guard','Sword_Idle',1.666667,False),('CombatWalk','Walk_Loop',1.333333,True),('Slash','Sword_Idle',.833333,True),('Heavy','Sword_Idle',1.1,True)]
clips=[];actions=[];s.render.fps=60
for name,action,duration,upper in spec:
 a=bpy.data.actions.new('A_Sword_'+name);actions.append(a);rig.animation_data.action=a
 end=1+round(duration*60);s.frame_start=1;s.frame_end=end
 for frame in range(1,end+1):
  phase=(frame-1)/(end-1);sampleframe=phase*float(bpy.data.actions[action].frame_range[1]);pose=sample(action,0 if name in ['Slash','Heavy'] else sampleframe)
  if upper:
   for n in mp:
    if not n.startswith(('thigh','calf','foot')) and n!='pelvis':pose[n]=guard[n]
  world={}
  for b in rig.data.bones:
   n=b.name;p=b.parent
   head=(world[p.name]@(rest[p.name].inverted()@rest[n].translation)) if p else rest[n].translation.copy()
   q=rest[n].to_quaternion()
   if n in mp:
    q=(C@pose[n].to_3x3()@base[n].to_3x3().inverted()@Ci@cal[n]).to_quaternion()
    if n=='pelvis':head.z+=max(-.09,min(.09,(pose[n].translation.z-base[n].translation.z)*.94))
   elif p:q=world[p.name].to_quaternion()@rest[p.name].to_quaternion().inverted()@q
   world[n]=Matrix.LocRotScale(head,q,Vector((1,1,1)))
  floor=min(world[n].translation.z for n in ['foot_L','foot_R']);dz=.15-floor
  for n in world:
   if n!='root':world[n].translation.z+=dz
  if name in ['Slash','Heavy']:
   time=(frame-1)/60
   curve=([(0,0,0),(.20,-24,-3),(.30,-20,-2),(.45,27,6),(.61,15,4),(.833333,0,0)] if name=='Slash' else [(0,0,0),(.32,-5,-10),(.55,-5,-10),(.74,8,25),(.87,6,18),(1.1,0,0)])
   twist=lean=0
   for (ta,ya,pa),(tb,yb,pb) in zip(curve,curve[1:]):
    if time<=tb+1e-5:
     w=max(0,min(1,(time-ta)/(tb-ta)));w=w*w*(3-2*w);twist=ya+(yb-ya)*w;lean=pa+(pb-pa)*w;break
   pivot=world['pelvis'].translation+Vector((0,0,.10));turn=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(twist),4,'Z')@Matrix.Rotation(math.radians(lean),4,'Y')@Matrix.Translation(-pivot)
   for n in list(world):
    if n.startswith(('spine','neck','head','upperarm','forearm','hand','lantern','lamp')):world[n]=turn@world[n]
  if upper or name=='Guard':
   time=(frame-1)/60
   # Blade orientation is independent of finger direction: +Z points along the blade,
   # +Y follows curled fingers. Two-bone IK holds the wrist without stretching the arm.
   h0=Vector((.24,-.27,1.12));d0=Vector((.72,-.10,.62))
   keys=[(0,h0,d0)]
   if name=='Slash':
    keys=[(0,h0,d0),(.19,Vector((.02,-.49,1.25)),Vector((-.8,-.5,.10))),(.30,Vector((.25,-.43,1.24)),Vector((.25,-.97,.02))),(.375,Vector((.46,-.09,1.23)),Vector((1,0,-.04))),(.45,Vector((.31,.27,1.22)),Vector((.20,.98,.02))),(.61,Vector((.15,.15,1.16)),Vector((-.45,.8,.15))),(.833333,h0,d0)]
   if name=='Heavy':
    keys=[(0,h0,d0),(.32,Vector((.04,-.26,1.73)),Vector((-.36,-.04,.94))),(.55,Vector((.04,-.26,1.73)),Vector((-.36,-.04,.94))),(.665,Vector((.44,-.15,1.19)),Vector((.63,.02,-.77))),(.74,Vector((.42,-.13,1.07)),Vector((.60,.02,-.80))),(.87,Vector((.31,-.15,1.04)),Vector((.63,.02,-.77))),(1.1,h0,d0)]
   hand=h0.copy();direction=d0.normalized()
   for (ta,ha,da),(tb,hb,db) in zip(keys,keys[1:]):
    if time<=tb+1e-5:
     w=max(0,min(1,(time-ta)/(tb-ta)));w=w*w*(3-2*w);hand=ha.lerp(hb,w);direction=da.lerp(db,w).normalized();break
   if name=='CombatWalk':hand.z+=world['pelvis'].translation.z-rest['pelvis'].translation.z
   root=world['upperarm_L'].translation;upperlen=rig.data.bones['upperarm_L'].length;lowerlen=rig.data.bones['forearm_L'].length
   delta=hand-root;distance=min(delta.length,upperlen+lowerlen-.006);axis=delta.normalized();hand=root+axis*distance
   pole=Vector((0,-1,-.1));bend=(pole-axis*pole.dot(axis)).normalized();along=(upperlen*upperlen-lowerlen*lowerlen+distance*distance)/(2*distance)
   elbow=root+axis*along+bend*math.sqrt(max(0,upperlen*upperlen-along*along))
   for n,start,finish in [('upperarm_L',root,elbow),('forearm_L',elbow,hand)]:
    rd=rig.data.bones[n].tail_local-rig.data.bones[n].head_local;q=rd.normalized().rotation_difference((finish-start).normalized())@rest[n].to_quaternion();world[n]=Matrix.LocRotScale(start,q,Vector((1,1,1)))
   finger=Vector((0,0,-1));finger=(finger-direction*finger.dot(direction))
   if finger.length<.1:finger=Vector((-1,0,0))
   finger.normalize();across=finger.cross(direction).normalized();finger=direction.cross(across).normalized()
   q=Matrix((across,finger,direction)).transposed().to_quaternion();world['hand_L']=Matrix.LocRotScale(hand,q,Vector((1,1,1)))
  for b in rig.pose.bones:
   b.rotation_mode='QUATERNION';b.matrix=world[b.name];bpy.context.view_layer.update()
   for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(O/('A_Sword_'+name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',primary_bone_axis='Y',secondary_bone_axis='X')
 clips.append({'name':'A_Sword_'+name,'file':'A_Sword_'+name+'.fbx','duration_seconds':(end-1)/60,'source':action,'upper_body_guard':upper})
(O/'animation-manifest.json').write_text(json.dumps({'skeleton':'/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton','animations':clips,'license':'Quaternius Universal Animation Library Standard, CC0; see SourceAssets/AnimationTrial/License.txt','root_motion':False},indent=2))
bpy.data.libraries.write(str(O/'SwordLocomotion.blend'),set(actions)|{rig.data,rig},compress=True,fake_user=True)
result={'clips':clips}
