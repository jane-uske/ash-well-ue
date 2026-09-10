"""Build centimetre-native copies of the existing hero and animation skeleton.
Run in a disposable background Blender process; no interactive scene is modified.
"""
import bpy,json,math,bmesh
from pathlib import Path
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/HeroComplete';O.mkdir(exist_ok=True)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01;s.render.fps=60
with bpy.data.libraries.load(str(R/'SourceAssets/SwordPass/TravellerPrepared.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith(('SK_Traveller','AW_Traveller_GameRig'))]
for ob in b.objects:s.collection.objects.link(ob)
rig=next(o for o in b.objects if o.type=='ARMATURE');body=next(o for o in b.objects if o.type=='MESH' and 'Cloak' not in o.name)
rig.animation_data_clear();rig.name='AW_HeroRig'
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
# Load the already reviewed cloak geometry separately.
with bpy.data.libraries.load(str(R/'SourceAssets/TravellerPolish/TravellerCloakPolish.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if 'Cloak' in n and not 'Rig' in n]
cloaks=[]
for ob in b.objects:
 if ob.type=='MESH':s.collection.objects.link(ob);cloaks.append(ob)
cape=cloaks[0]
for ob in [body,cape]:
 ob.parent=rig;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 for v in ob.data.vertices:v.co*=100
 for p in ob.data.polygons:p.use_smooth=True
 ob.data.normals_split_custom_set([(0,0,0)]*len(ob.data.loops))
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:b.head*=100;b.tail*=100
bpy.ops.object.mode_set(mode='OBJECT')
# Bake the historical component Y mirror into geometry/rest transforms. D keeps each bone basis right handed.
Reflect=Matrix.Diagonal((1,-1,1,1));D=Matrix.Diagonal((-1,1,1,1))
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:b.matrix=Reflect@b.matrix@D
bpy.ops.object.mode_set(mode='OBJECT')
for ob in [body,cape]:
 ob.data.transform(Reflect);bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
report={'units':'centimetres','skeleton_root_scale':1,'animations':[]}
def export(path,objects,anim=False):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=anim,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',primary_bone_axis='Y',secondary_bone_axis='X')
export(O/'SK_Hero.fbx',[rig,body]);export(O/'SK_HeroCloak.fbx',[rig,cape])
# Preserve the established combat timings while normalizing all fallback clips.
for blend,prefix,names in [('SwordPass/SwordLocomotion.blend','A_Sword_',['Idle','Walk','Run','Sprint','Guard','CombatWalk','Slash','Heavy']),('BattlePolish/BattlePlayerAnimations.blend','A_Battle_',['Dodge','Hit']),('CombatCharacters/CombatAnimations.blend','A_Combat_Protagonist_',['Death'])]:
 with bpy.data.libraries.load(str(R/'SourceAssets'/blend),link=False) as (a,b):b.actions=[n for n in a.actions if n.split('.')[0] in [prefix+k for k in names]]
 for action in b.actions:
  name=action.name.split('.')[0].removeprefix(prefix);rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      if fc.data_path.endswith('.location'):
       for k in fc.keyframe_points:
        factor=-100 if fc.array_index==0 else 100
        k.co.y*=factor;k.handle_left.y*=factor;k.handle_right.y*=factor
      elif fc.data_path.endswith('.rotation_quaternion') and fc.array_index in (2,3):
       for k in fc.keyframe_points:k.co.y*=-1;k.handle_left.y*=-1;k.handle_right.y*=-1
  s.frame_start=round(action.frame_range[0]);s.frame_end=round(action.frame_range[1]);s.frame_set(s.frame_start)
  export(O/f'A_Hero_{name}.fbx',[rig],True)
  report['animations'].append({'name':name,'source':blend,'duration':(s.frame_end-s.frame_start)/60})
rig.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'HeroNormalized.blend'))
(O/'manifest.json').write_text(json.dumps(report,indent=2))
print('HERO_NORMALIZED',json.dumps(report))
