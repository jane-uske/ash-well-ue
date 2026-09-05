import json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
result={}
try:
    options=u.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type',False)
    options.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property('import_as_skeletal',False)
    options.set_editor_property('import_materials',False)
    options.set_editor_property('import_textures',False)
    options.static_mesh_import_data.set_editor_property('convert_scene_unit',True)
    task=u.AssetImportTask();task.filename=str(ROOT/'SourceAssets/CombatGeometry/SM_Combat_ArmorBlock.fbx')
    task.destination_path='/Game/AshWell/Combat/Geometry';task.destination_name='SM_Combat_ArmorBlock'
    task.automated=True;task.replace_existing=True;task.save=True;task.options=options;task.factory=u.FbxFactory()
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=u.EditorAssetLibrary.load_asset('/Game/AshWell/Combat/Geometry/SM_Combat_ArmorBlock')
    assert isinstance(mesh,u.StaticMesh)
    result={'state':'completed','asset':mesh.get_path_name(),'extent':str(mesh.get_bounds().box_extent)}
except Exception:
    result={'state':'failed','error':traceback.format_exc()};u.log_error(result['error'])
(ROOT/'Saved/Automation/combat-geometry-report.json').write_text(json.dumps(result,indent=2))
u.SystemLibrary.quit_editor()
