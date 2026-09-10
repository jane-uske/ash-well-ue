"""Sample Meshy presets onto the normalized hero. Keep download lineage in manifest."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/HeroComplete';source=R/'meshy_output/20260910_224236_ashwell-hero-complete-motion_01a08bc5'
bpy.ops.wm.open_mainfile(filepath=str(O/'HeroNormalized.blend'));targetscene=bpy.context.scene;rig=bpy.data.objects['AW_HeroRig'];rig.animation_data_create();rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
C=Matrix(((0,-1,0),(-1,0,0),(0,0,1)));Ci=C.inverted()
mp={'pelvis':'Hips','spine_01':'Spine02','spine_02':'Spine','neck':'neck','head':'Head'}
for t,s in [('L','Right'),('R','Left')]:
 for a,b in [('upperarm','Arm'),('forearm','ForeArm'),('hand','Hand'),('thigh','UpLeg'),('calf','Leg'),('foot','Foot')]:mp[a+'_'+t]=s+b
child={'Hips':'Spine02','Spine02':'Spine01','Spine':'neck','neck':'Head','Head':'head_end'}
for s in ['Left','Right']:
 for a,b in [('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:child[s+a]=s+b
report=[]
for name in ['Idle','Run','Jump','Dodge','Slash','Heavy','CombatWalk','Walk']:
 file=source/(name+'.glb') if name!='Walk' else R/'meshy_output/20260910_203249_ashwell-traveller-sword-v01_01a08b48/walking.glb'
 sc=bpy.data.scenes.new('MeshySource'+name);bpy.context.window.scene=sc;sc.render.fps=60
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(file));new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE');act=src.animation_data.action;start,end=act.frame_range;duration=(end-start)/60
 sr={b.name:src.matrix_world@b.matrix_local for b in src.data.bones}
 cal={}
 for n,v in mp.items():
  b=rig.data.bones[n];sd=(sr[child[v]].translation-sr[v].translation) if v in child else src.matrix_world.to_3x3()@(src.data.bones[v].tail_local-src.data.bones[v].head_local)
  cal[n]=(b.tail_local-b.head_local).normalized().rotation_difference((C@sd).normalized()).to_matrix()@rest[n].to_3x3()
 # Source clips begin/end in standing poses. Keep complete movement, remapped to combat duration.
 outduration={'Dodge':.5833333,'Slash':.8333333,'Heavy':1.1,'Jump':.85}.get(name,duration)
 action=bpy.data.actions.new('A_Hero_Meshy'+name);rig.animation_data.action=action
 targetscene.frame_start=1;targetscene.frame_end=1+round(outduration*60);targetscene.render.fps=60
 samples=[]
 for frame in range(1,targetscene.frame_end+1):
  phase=(frame-1)/(targetscene.frame_end-1);sf=start+(end-start)*phase;sc.frame_set(int(sf),subframe=sf-int(sf));bpy.context.view_layer.update()
  pose={n:src.matrix_world@src.pose.bones[v].matrix for n,v in mp.items()};world={}
  for b in rig.data.bones:
   n=b.name;p=b.parent;head=world[p.name]@(rest[p.name].inverted()@rest[n].translation) if p else rest[n].translation.copy();q=rest[n].to_quaternion()
   if n in mp:
    v=mp[n];q=(C@pose[n].to_quaternion().to_matrix()@sr[v].to_quaternion().to_matrix().inverted()@Ci@cal[n]).to_quaternion()
    if n=='pelvis':head.z+=(pose[n].translation.z-sr[v].translation.z)*100*.92
   elif p:q=world[p.name].to_quaternion()@rest[p.name].to_quaternion().inverted()@q
   world[n]=Matrix.LocRotScale(head,q,Vector((1,1,1)))
  if name=='Dodge':dz=max(0,9-min(world[n].translation.z for n in mp))
  else:dz=13-min(world[n].translation.z for n in ['foot_L','foot_R'])
  # Airborne height comes from CharacterMovement; preserve the bent-leg jump silhouette.
  if name=='Jump':dz=88-world['pelvis'].translation.z
  for n in world:
   if n!='root':world[n].translation.z+=dz
  bpy.context.window.scene=targetscene
  for b in rig.pose.bones:
   b.rotation_mode='QUATERNION';b.matrix=world[b.name];bpy.context.view_layer.update()
   for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
  if frame in [1,round(targetscene.frame_end/2),targetscene.frame_end]:samples.append({'phase':phase,'head':list(world['head'].translation),'hand':list(world['hand_L'].translation)})
  bpy.context.window.scene=sc
 bpy.context.window.scene=targetscene;targetscene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(O/f'A_Hero_Meshy{name}.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL')
 report.append({'name':name,'source_file':str(file),'source_seconds':duration,'duration':outduration,'samples':samples});print('MESHY_RETARGET',json.dumps(report[-1]),flush=True)
(O/'meshy-motion-manifest.json').write_text(json.dumps(report,indent=2))
bpy.data.libraries.write(str(O/'HeroMeshyMotion.blend'),{targetscene}|set(bpy.data.actions),compress=True,fake_user=True)
