"""Reimport only the charge sequence; preserve native Montage/Notify and other moves."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';D=B+'/ReferenceProduction';report={}
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    skin=u.EditorAssetLibrary.load_asset(B+'/SK_SampleKnight');opt=u.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_as_skeletal':True,'import_mesh':False,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
    opt.skeleton=skin.get_editor_property('skeleton')
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_default_sample_rate':False,'custom_sample_rate':60}.items():opt.anim_sequence_import_data.set_editor_property(k,v)
    name='A_ReferenceRider_ChargeSweep';task=u.AssetImportTask();task.filename=str(R/'SourceAssets/MountedReferenceProduction/ProportionRevision'/(name+'.fbx'));task.destination_path=D;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.replace_existing_settings=True;task.options=opt;task.factory=u.FbxFactory()
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);clip=u.EditorAssetLibrary.load_asset(D+'/'+name)
    assert abs(clip.get_editor_property('sequence_length')-5.8)<.001
    u.AshWellReferenceEnvironmentTools.finish_asset_compilation()
    report={'passed':True,'clip':clip.get_path_name(),'seconds':clip.get_editor_property('sequence_length'),'scope':'Only charge rider sequence reimported; existing native Montage, Notify, horse sequence, and other attacks retained. Needs fresh runtime validation.'}
except Exception:report={'passed':False,'error':traceback.format_exc()};u.log_error(report['error'])
(R/'Saved/MountedReferenceProduction/proportion-import.json').write_text(json.dumps(report,indent=2)+'\n')
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.monotonic()
def finish(dt):
    if time.monotonic()-started>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
