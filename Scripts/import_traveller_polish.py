"""Import only the derived cloak and its material; preserve the playable body/rig."""
from pathlib import Path
import unreal as u, json
R = Path(__file__).resolve().parents[1]
O = R / 'SourceAssets/TravellerPolish'
B = '/Game/AshWell/Combat/SwordPass'
ed = u.EditorAssetLibrary
L = u.MaterialEditingLibrary
at = u.AssetToolsHelpers.get_asset_tools()
u.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.FBX 0')
m = ed.load_asset(B + '/M_TravellerCloak')
assert m
L.delete_all_material_expressions(m)
m.set_editor_property('used_with_skeletal_mesh', True)
m.set_editor_property('two_sided', True)
m.set_editor_property('tangent_space_normal', False)
m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
def scalar(value, prop):
    n=L.create_material_expression(m,u.MaterialExpressionConstant)
    n.r=value
    assert L.connect_material_property(n,'',prop)
n=L.create_material_expression(m,u.MaterialExpressionConstant3Vector)
n.constant=u.LinearColor(.010,.013,.017,1)
assert L.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR)
scalar(.92,u.MaterialProperty.MP_ROUGHNESS)
scalar(.12,u.MaterialProperty.MP_SPECULAR)
scalar(0,u.MaterialProperty.MP_METALLIC)
# Preserve the already-tested compatibility normal path while the legacy
# mirrored/root-scaled skeleton is still in use. Subdivided folds remove the
# large planar breaks instead of re-enabling the broken tangent map.
pos=L.create_material_expression(m,u.MaterialExpressionWorldPosition)
dx=L.create_material_expression(m,u.MaterialExpressionDDX)
dy=L.create_material_expression(m,u.MaterialExpressionDDY)
cross=L.create_material_expression(m,u.MaterialExpressionCrossProduct)
normal=L.create_material_expression(m,u.MaterialExpressionNormalize)
for a,out,b,inp in [(pos,'XYZ',dx,'Value'),(pos,'XYZ',dy,'Value'),(dy,'',cross,'A'),(dx,'',cross,'B'),(cross,'',normal,'VectorInput')]:
    assert L.connect_material_expressions(a,out,b,inp)
assert L.connect_material_property(normal,'',u.MaterialProperty.MP_NORMAL)
L.recompile_material(m)
ed.save_loaded_asset(m)
opts=u.FbxImportUI()
for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'import_as_skeletal':True,'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':ed.load_asset('/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton')}.items():
    opts.set_editor_property(k,v)
d=opts.skeletal_mesh_import_data
for k,v in {'update_skeleton_reference_pose':False,'convert_scene':True,'convert_scene_unit':True,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS}.items():
    d.set_editor_property(k,v)
t=u.AssetImportTask()
t.filename=str(O/'SK_TravellerCloak.fbx')
t.destination_path=B
t.destination_name='SK_TravellerCloak'
t.automated=True
t.save=True
t.replace_existing=True
t.replace_existing_settings=True
t.options=opts
t.factory=u.FbxFactory()
at.import_asset_tasks([t])
mesh=ed.load_asset(B+'/SK_TravellerCloak')
assert isinstance(mesh,u.SkeletalMesh)
slots=mesh.get_editor_property('materials')
while len(slots)<2:
    slots.append(u.SkeletalMaterial(material_interface=m,material_slot_name='ImportedCloth'))
for slot in slots:
    slot.set_editor_property('material_interface',m)
mesh.set_editor_property('materials',slots)
mesh.set_editor_property('positive_bounds_extension',u.Vector(100,80,195))
mesh.set_editor_property('negative_bounds_extension',u.Vector(100,80,15))
ns=mesh.get_editor_property('nanite_settings')
ns.set_editor_property('enabled',False)
mesh.set_editor_property('nanite_settings',ns)
ed.save_loaded_asset(mesh)
report={'mesh':mesh.get_path_name(),'material':m.get_path_name(),'source':str(O/'SK_TravellerCloak.fbx'),'slots':len(slots),'scope':'cloak geometry and cloth material only'}
(R/'Saved/TravellerPolish/import.json').write_text(json.dumps(report,indent=2))
u.log('TRAVELLER_POLISH_IMPORTED')
