"""Blender: reusable original chamfered armour block; one metre bounding box."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets/CombatGeometry';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.mesh.primitive_cube_add(size=1)
obj=bpy.context.object;obj.name='SM_Combat_ArmorBlock'
mod=obj.modifiers.new('Rounded cast metal edges','BEVEL');mod.width=.055;mod.segments=3
bpy.ops.object.modifier_apply(modifier=mod.name)
mod=obj.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CombatArmor.blend'))
bpy.ops.export_scene.fbx(filepath=str(OUT/'SM_Combat_ArmorBlock.fbx'),use_selection=True,
    object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
    add_leaf_bones=False,bake_anim=False)
print({'mesh':obj.name,'vertices':len(obj.data.vertices),'dimensions':list(obj.dimensions)})
