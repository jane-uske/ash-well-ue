"""Import only the reversible mounted rider derivative through shared UE owner."""
from pathlib import Path
import json,unreal as u
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedBoss';N='SK_MountedRider'
ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools()
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
o=u.FbxImportUI()
for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'import_as_skeletal':True,'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():o.set_editor_property(k,v)
d=o.skeletal_mesh_import_data
for k,v in {'convert_scene':False,'convert_scene_unit':False,'import_uniform_scale':1,'update_skeleton_reference_pose':True}.items():d.set_editor_property(k,v)
d.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS)
d.set_editor_property('normal_generation_method',u.FBXNormalGenerationMethod.MIKK_T_SPACE)
t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedBoss/SK_MountedRider.fbx');t.destination_path=B;t.destination_name=N;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=o;t.factory=u.FbxFactory()
at.import_asset_tasks([t]);mesh=ed.load_asset(B+'/'+N);assert mesh,N
body=ed.load_asset('/Game/AshWell/Combat/WardenHQ/M_WardenHQ');inner=ed.load_asset('/Game/AshWell/Combat/WardenHQ/M_WardenHQ_Inner');assert body and inner
slots=mesh.get_editor_property('materials')
for i,slot in enumerate(slots):slot.material_interface=body if i==0 else inner
mesh.set_editor_property('materials',slots)
ns=mesh.get_editor_property('nanite_settings');ns.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',ns)
mesh.set_editor_property('positive_bounds_extension',u.Vector(45,45,30));mesh.set_editor_property('negative_bounds_extension',u.Vector(45,45,30))
ed.save_loaded_asset(mesh);ed.save_loaded_asset(mesh.get_editor_property('skeleton'))
report={'path':mesh.get_path_name(),'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'material_slots':len(slots),'status':'imported; seated runtime visual check pending'}
(R/'Saved/MountedBoss/mounted-rider-import.json').write_text(json.dumps(report,indent=2));u.log('MOUNTED_RIDER_IMPORTED '+json.dumps(report))
