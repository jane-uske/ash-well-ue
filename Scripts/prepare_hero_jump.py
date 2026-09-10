"""Dedicated Quaternius jump phases retargeted onto our centimetre-native hero."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/JumpPolish'
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceAssets/HeroComplete/HeroNormalized.blend'))
ts=bpy.context.scene;rig=bpy.data.objects['AW_HeroRig'];rig.animation_data_create()
ss=bpy.data.scenes.new('QuaterniusJumpSource');ss.render.fps=60;bpy.context.window.scene=ss
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'SourceAssets/AnimationTrial/AnimationLibrary_Standard.glb'));src=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE')
for t in src.animation_data.nla_tracks:t.mute=True
acts={n:next(a for a in bpy.data.actions if a.name.split('.')[0]==n) for n in ['Jump_Start','Jump_Loop','Jump_Land']}
report={}
for n,a in acts.items():
 src.animation_data.action=a;src.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;samples=[]
 for phase in [0,.2,.4,.6,.8,1]:
  f=lo+(hi-lo)*phase;ss.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  samples.append({'t':(f-lo)/60,'bones':{k:list(src.pose.bones[k].head) for k in ['DEF-hips','DEF-shin.L','DEF-foot.L','DEF-shin.R','DEF-foot.R']}})
 report[n]={'range':[lo,hi],'samples':samples}
(O/'source-inspect.json').write_text(json.dumps(report,indent=2));print('JUMP_SOURCE',json.dumps(report),flush=True)
if '--inspect' in sys.argv:sys.exit()
C=Matrix(((0,-1,0),(-1,0,0),(0,0,1)));Ci=C.inverted()
mp={'pelvis':'DEF-hips','spine_01':'DEF-spine.002','spine_02':'DEF-spine.003','neck':'DEF-neck','head':'DEF-head'}
for side,suffix in [('L','R'),('R','L')]:
 for target,source in [('upperarm','upper_arm'),('forearm','forearm'),('hand','hand'),('thigh','thigh'),('calf','shin'),('foot','foot')]:mp[target+'_'+side]='DEF-'+source+'.'+suffix
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};base={n:src.data.bones[v].matrix_local.copy() for n,v in mp.items()};cal={}
for n,v in mp.items():
 b=rig.data.bones[n];sb=src.data.bones[v]
 cal[n]=(b.tail_local-b.head_local).normalized().rotation_difference((C@(sb.tail_local-sb.head_local)).normalized()).to_matrix()@rest[n].to_3x3()
def sample(name,frame):
 bpy.context.window.scene=ss;a=acts[name];src.animation_data.action=a;src.animation_data.action_slot=a.slots[0]
 ss.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 return {n:src.pose.bones[v].matrix.copy() for n,v in mp.items()}
def blend(a,b,t):
 return {n:Matrix.LocRotScale(a[n].translation.lerp(b[n].translation,t),a[n].to_quaternion().slerp(b[n].to_quaternion(),t),Vector((1,1,1))) for n in a}
tuck=sample('Jump_Start',16);extend=sample('Jump_Loop',0);stand=sample('Jump_Land',65)
clips=[]
for name,duration in [('JumpTakeoff',.14),('JumpAir',.4),('JumpLand',.26)]:
 action=bpy.data.actions.new('A_Hero_'+name);rig.animation_data.action=action
 ts.frame_start=1;ts.frame_end=round(duration*60)+1;ts.render.fps=60
 samples=[]
 for frame in range(1,ts.frame_end+1):
  t=(frame-1)/(ts.frame_end-1)
  if name=='JumpTakeoff':pose=sample('Jump_Start',4+12*t)
  elif name=='JumpAir':pose=blend(tuck,extend,t*t*(3-2*t))
  else:pose=blend(stand,sample('Jump_Land',65*t),.55)
  world={}
  for b in rig.data.bones:
   n=b.name;p=b.parent;head=world[p.name]@(rest[p.name].inverted()@rest[n].translation) if p else rest[n].translation.copy();q=rest[n].to_quaternion()
   if n in mp:q=(C@pose[n].to_quaternion().to_matrix()@base[n].to_quaternion().to_matrix().inverted()@Ci@cal[n]).to_quaternion()
   elif p:q=world[p.name].to_quaternion()@rest[p.name].to_quaternion().inverted()@q
   world[n]=Matrix.LocRotScale(head,q,Vector((1,1,1)))
  dz=13-min(world[n].translation.z for n in ['foot_L','foot_R']) if name=='JumpLand' else 88-world['pelvis'].translation.z
  for n in world:
   if n!='root':world[n].translation.z+=dz
  bpy.context.window.scene=ts
  for b in rig.pose.bones:
   b.rotation_mode='QUATERNION';b.matrix=world[b.name];bpy.context.view_layer.update()
   for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
  samples.append({'time':(frame-1)/60,'left_foot':list(world['foot_L'].translation),'right_foot':list(world['foot_R'].translation)})
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;ts.frame_set(1)
 bpy.ops.export_scene.fbx(filepath=str(O/f'A_Hero_{name}.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL')
 clips.append({'name':name,'duration':(ts.frame_end-1)/60,'samples':samples})
(O/'manifest.json').write_text(json.dumps({'source':'Quaternius Universal Animation Library Standard, CC0','files':['Jump_Start','Jump_Loop','Jump_Land'],'air':'One monotonic tuck-to-descent blend, never a running cycle','clips':clips},indent=2))
bpy.data.libraries.write(str(O/'HeroJumpPhases.blend'),{ts}|set(bpy.data.actions),compress=True,fake_user=True)
print('JUMP_PHASES_EXPORTED',[(x['name'],x['duration']) for x in clips],flush=True)
