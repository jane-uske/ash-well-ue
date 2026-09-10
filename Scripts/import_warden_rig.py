"""Import only the prepared skeletal visual into an isolated asset directory."""
import unreal as u, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='/Game/AshWell/Combat/WardenRig'
ed=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools()
for n in ['M_WardenHQ','M_WardenHQ_Inner']:
 mat=ed.load_asset('/Game/AshWell/Combat/WardenHQ/'+n)
 mat.set_editor_property('used_with_skeletal_mesh',True)
 u.MaterialEditingLibrary.recompile_material(mat);ed.save_loaded_asset(mat)
opts=u.FbxImportUI()
for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,
 'import_as_skeletal':True,'import_mesh':True,'import_animations':False,'import_materials':False,
 'import_textures':False,'create_physics_asset':False}.items():opts.set_editor_property(k,v)
for k,v in {'convert_scene':False,'convert_scene_unit':False,'force_front_x_axis':False,'import_uniform_scale':1.0,
 'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():opts.skeletal_mesh_import_data.set_editor_property(k,v)
t=u.AssetImportTask();t.filename=str(ROOT/'SourceAssets/WardenRig/SK_WardenRig.fbx');t.destination_path=BASE
t.destination_name='SK_WardenRig';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory()
tools.import_asset_tasks([t]);mesh=ed.load_asset(BASE+'/SK_WardenRig');assert isinstance(mesh,u.SkeletalMesh)
materials=mesh.get_editor_property('materials')
for i,slot in enumerate(materials):
 name=str(slot.get_editor_property('imported_material_slot_name')).lower()
 slot.set_editor_property('material_interface',ed.load_asset('/Game/AshWell/Combat/WardenHQ/M_WardenHQ_Inner' if 'interior' in name or 'cap' in name or 'inner' in name else '/Game/AshWell/Combat/WardenHQ/M_WardenHQ'))
 materials[i]=slot
mesh.set_editor_property('materials',materials)
ed.save_loaded_asset(mesh);ed.save_loaded_asset(mesh.skeleton)
report={'asset':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'materials':[str(s.get_editor_property('imported_material_slot_name')) for s in materials]}
(ROOT/'Saved/Polish/rig-import.json').write_text(json.dumps(report,indent=2))
u.log('ASHWELL_RIG_IMPORTED '+json.dumps(report))
