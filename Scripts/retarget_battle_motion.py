"""Retarget downloaded Meshy presets onto our existing protagonist; no new character mesh."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/BattlePolish';S=R/'meshy_output/20260909_battle_motion_v01'
data=json.loads((S/'source-motion-samples.json').read_text())
scene=bpy.data.scenes.new('AW_BattlePlayer_Retarget');bpy.context.window.scene=scene
with bpy.data.libraries.load(str(R/'SourceAssets/CombatCharacters/CombatAnimations.blend'),link=False) as (a,b):b.objects=['SK_Intro_Protagonist_Rig','SK_Intro_Protagonist']
for o in b.objects:scene.collection.objects.link(o)
rig=next(o for o in b.objects if o.type=='ARMATURE');mesh=next(o for o in b.objects if o.type=='MESH');rig.name='AW_BattlePlayer_Rig';mesh.name='AW_BattlePlayer'
if not any(m.type=='ARMATURE' for m in mesh.modifiers):m=mesh.modifiers.new('Skin','ARMATURE');m.object=rig
rig.animation_data_create();rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
neutral={b.name:b.matrix.copy() for b in rig.pose.bones}
C=Matrix(((0,-1,0),(-1,0,0),(0,0,1)))
mapping={'pelvis':'Hips','spine_01':'Spine02','spine_02':'Spine','neck':'neck','head':'Head','upperarm_L':'LeftArm','forearm_L':'LeftForeArm','hand_L':'LeftHand','upperarm_R':'RightArm','forearm_R':'RightForeArm','hand_R':'RightHand','thigh_L':'LeftUpLeg','calf_L':'LeftLeg','foot_L':'LeftFoot','thigh_R':'RightUpLeg','calf_R':'RightLeg','foot_R':'RightFoot'}
FPS=60
spec={'Slash':(.8333333,[(0,1),(.30,20),(.45,33),(.72,47),(.8333333,48)]),'Heavy':(1.10,[(0,1),(.55,34),(.72,46),(1.1,56)]),'Dodge':(.5833333,[(0,12),(.10,19),(.34,37),(.48,49),(.5833333,56)]),'Hit':(.45,[(0,1),(.10,12),(.45,46)])}
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def sample(name,f):
 rows=data[name]['samples'];i=max(0,min(len(rows)-1,int(f)-1));j=min(i+1,len(rows)-1);a=f-int(f);out={}
 for k,v in rows[i]['bones'].items():
  w=rows[j]['bones'][k];M=Matrix(v['matrix']);N=Matrix(w['matrix']);q=M.to_quaternion().slerp(N.to_quaternion(),a)
  out[k]={'head':Vector(v['head']).lerp(Vector(w['head']),a),'tail':Vector(v['tail']).lerp(Vector(w['tail']),a),'q':q}
 return out
clips=[];qa={};new_actions=[]
for name,(duration,keys) in spec.items():
 source={'Heavy':'Hammer','Dodge':'Roll'}.get(name,name);act=bpy.data.actions.new('A_Battle_'+name);new_actions.append(act);rig.animation_data.action=act;end=1+round(duration*FPS);scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=end
 poses=[]
 for frame in range(1,end+1):
  time=(frame-1)/FPS
  for (ta,fa),(tb,fb) in zip(keys,keys[1:]):
   if time<=tb+1e-4:sf=fa+(fb-fa)*max(0,min(1,(time-ta)/(tb-ta)));break
  else:sf=keys[-1][1]
  src=sample(source,sf);base=sample(source,1);hip=src['Hips']['head'];weight=min(smooth(time/.08),smooth((duration-time)/.10));poseM={}
  for b in rig.data.bones:
   n=b.name;parent=b.parent;rh=rest[n].translation
   if parent:
    pm=poseM[parent.name];head=pm@(rest[parent.name].inverted()@rh)
   else:head=rh.copy()
   q=rest[n].to_quaternion()
   if n in mapping:
    srcname=mapping[n];d=C@(src[srcname]['tail']-src[srcname]['head']);rd=(b.tail_local-b.head_local).normalized();q=rd.rotation_difference(d.normalized())@q
    refdir=C@(base[srcname]['tail']-base[srcname]['head']);refaim=rd.rotation_difference(refdir.normalized())@rest[n].to_quaternion()
    reflect=Matrix(((-1,0,0),(0,1,0),(0,0,1)))
    firstq=(C@base[srcname]['q'].to_matrix()@reflect).to_quaternion();currentq=(C@src[srcname]['q'].to_matrix()@reflect).to_quaternion()
    q=currentq@firstq.inverted()@refaim
    if n=='pelvis':head=rh+Vector((0,0,(hip.z-base['Hips']['head'].z)*.92))
   elif parent:q=poseM[parent.name].to_quaternion()@rest[parent.name].to_quaternion().inverted()@q
   if n.startswith('lantern') or n.startswith('lamp_light'):q=rest[n].to_quaternion()
   target=Matrix.LocRotScale(head,q,Vector((1,1,1)))
   # Smooth authored neutral-to-action transitions; preserve root identity.
   if n!='root':target=Matrix.LocRotScale(neutral[n].translation.lerp(head,weight),neutral[n].to_quaternion().slerp(q,weight),Vector((1,1,1)))
   poseM[n]=target
  # Keep soles above the floor; mesh soles sit below foot-bone heads.
  if name!='Dodge':
   floor=min(poseM['foot_L'].translation.z,poseM['foot_R'].translation.z);dz=max(-.40,min(.30,.13-floor))
   for n in poseM:
    if n!='root':poseM[n].translation.z+=dz*weight
  if name=='Dodge':
   bottom=min(poseM[n].translation.z for n in mapping);dz=max(0,.10-bottom)
   for n in poseM:
    if n!='root':poseM[n].translation.z+=dz
  for b in rig.pose.bones:
   b.rotation_mode='QUATERNION';b.matrix=poseM[b.name];bpy.context.view_layer.update();b.keyframe_insert('location',frame=frame);b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('scale',frame=frame)
  if frame in [1,round(end*.3),round(end*.5),round(end*.7),end]:poses.append({'frame':frame,'hand':list(poseM['hand_L'].translation),'foot_min':min(poseM['foot_L'].translation.z,poseM['foot_R'].translation.z)})
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 original_name=rig.name;occupied=bpy.data.objects.get('SK_Intro_Protagonist_Rig')
 if occupied and occupied!=rig:occupied.name='AW_Archive_Rig'
 rig.name='SK_Intro_Protagonist_Rig'
 bpy.ops.export_scene.fbx(filepath=str(O/f'A_Battle_{name}.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',primary_bone_axis='Y',secondary_bone_axis='X')
 rig.name=original_name
 if occupied and occupied!=rig:occupied.name='SK_Intro_Protagonist_Rig'
 clips.append({'name':'A_Battle_'+name,'file':'A_Battle_'+name+'.fbx','source_preset':source,'duration_seconds':(end-1)/FPS,'frames':[1,end]});qa[name]=poses
# Warden feet and torso curves, sampled from the same motion source, adapted in C++ to rigid armour.
lines=['// Meshy presets 103 and 128; source units metres, horizontal root travel removed.','namespace BattleMotion {','struct FSample { float T, Forward, Lift, Pitch; };']
for name,source,start,end in [('Kick','Kick',1,71),('Hammer','Hammer',1,56)]:
 base=sample(source,start);init=base['RightFoot']['head']-base['Hips']['head'];lines.append('static const FSample '+name+'[] = {')
 for f in range(start,end+1):
  s=sample(source,f);v=s['RightFoot']['head']-s['Hips']['head']-init;sp=s['Spine']['tail']-s['Hips']['head'];pitch=math.degrees(math.atan2(-sp.y,sp.z));lines.append('{%.6ff,%.6ff,%.6ff,%.6ff},'%((f-start)/(end-start),-v.y*100,v.z*100,max(-30,min(38,pitch))))
 lines.append('};')
lines.append('}')
(R/'Source/AshWell/BattleMotionSamples.inl').write_text('\n'.join(lines)+'\n')
(O/'animation-manifest.json').write_text(json.dumps({'skeleton':'/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton','animations':clips,'source':'Meshy API presets on Quaternius carrier, retargeted and phase-remapped locally','root_motion':False},indent=2)+'\n')
(O/'retarget-pose-report.json').write_text(json.dumps(qa,indent=2))
scene.frame_set(1);bpy.data.libraries.write(str(O/'BattlePlayerAnimations.blend'),{scene}|set(new_actions),compress=True,fake_user=True)
result={'clips':clips,'pose_checks':qa}
