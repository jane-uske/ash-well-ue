"""Build a skin-ready copy in the inspected AW_WardenRig_Work scene via Blender MCP.
Preserves the approved source, its textures and independent hammer mesh.
"""
import bpy, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets/WardenRig'; OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.data.scenes.new('AW_WardenRig_Work')
with bpy.data.libraries.load(str(ROOT/'SourceAssets/WardenHQ/WardenHQ_Prepared.blend'),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith('SM_WardenHQ_')]
for obj in dst.objects:
 if obj is not None:scene.collection.objects.link(obj)
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
parts={o.name.removeprefix('SM_WardenHQ_').split('.')[0]:o for o in scene.objects if o.type=='MESH'}
assert len(parts)==12
arm=bpy.data.armatures.new('WardenRig');rig=bpy.data.objects.new('WardenRig',arm)
scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
root=arm.edit_bones.new('root');root.head=(0,0,0);root.tail=(0,0,10)
for name in parts:
 b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,0,10);b.parent=root
bpy.ops.object.mode_set(mode='OBJECT')
manifest=json.loads((ROOT/'SourceAssets/WardenHQ/warden_manifest.json').read_text())
joints=manifest['blender_rh_joints_cm']
parents={'RightUpperArm':('Body','RightShoulder'),'RightForearm':('RightUpperArm','RightElbow'),
 'LeftUpperArm':('Body','LeftShoulder'),'LeftForearm':('LeftUpperArm','LeftElbow'),
 'RightThigh':('Body','RightHip'),'RightShin':('RightThigh','RightKnee'),
 'LeftThigh':('Body','LeftHip'),'LeftShin':('LeftThigh','LeftKnee')}
weighted=0
for name,obj in parts.items():
 if name=='Hammer':continue
 g=obj.vertex_groups.new(name=name)
 g.add(list(range(len(obj.data.vertices))),1.,'REPLACE')
 if name in parents:
  parent,joint=parents[name];other=obj.vertex_groups.new(name=parent);p=Vector(joints[joint])
  for v in obj.data.vertices:
   d=(v.co-p).length
   if d<11:
    w=.45*(1-d/11);g.add([v.index],1-w,'REPLACE');other.add([v.index],w,'REPLACE');weighted+=1
 obj.select_set(True)
rig.select_set(False);parts['Hammer'].select_set(False)
bpy.context.view_layer.objects.active=parts['Body'];bpy.ops.object.join()
mesh=bpy.context.object;mesh.name='SK_WardenRig'
mod=mesh.modifiers.new('WardenSkin','ARMATURE');mod.object=rig;mesh.parent=rig
rig.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_WardenRig.fbx'),use_selection=True,
 object_types={'MESH','ARMATURE'},use_space_transform=False,axis_forward='X',axis_up='Z',
 add_leaf_bones=False,bake_anim=False,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE')
report={'bones':list(arm.bones.keys()),'vertices':len(mesh.data.vertices),
 'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'blended_joint_vertices':weighted,
 'hammer':'Existing independent SM_WardenHQ_Hammer; driven by same grip transform',
 'coordinate_contract':'RH centimetres; UE import convert_scene=False, convert_scene_unit=False'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
# Write only this production scene, not the unrelated open animation trial.
bpy.data.libraries.write(str(OUT/'WardenRig.blend'),{scene},fake_user=True)
result=report
