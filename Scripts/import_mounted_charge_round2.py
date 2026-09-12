"""Update only the two rider sequences, sample sockets and native speed blend.

Run after the game has exited and the module has been rebuilt. Original exports,
retarget assets, action timing and the other five moves are not reimported.
"""
from pathlib import Path
import json, traceback
import os
import unreal as u

R=Path(__file__).resolve().parents[1]
B='/Game/AshWell/Combat/MountedChargeSample'
ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();report={}
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    knight=ED.load_asset(B+'/SK_SampleKnight');skeleton=knight.get_editor_property('skeleton')
    for name in ['A_SampleRider_SeatedIdle','A_SampleRider_ChargeSweep']:
        opt=u.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,
                    'import_as_skeletal':True,'import_mesh':False,'import_animations':True,
                    'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
        opt.skeleton=skeleton;d=opt.anim_sequence_import_data
        for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_default_sample_rate':False,'custom_sample_rate':60}.items():d.set_editor_property(k,v)
        t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedChargeSample/Round2'/(name+'.fbx'))
        t.destination_path=B;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
        t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
        clip=ED.load_asset(B+'/'+name);assert clip
        report[name]={'seconds':clip.get_editor_property('sequence_length'),'source':t.filename}
    assert abs(report['A_SampleRider_ChargeSweep']['seconds']-3.55)<.002
    assert u.AshWellMountedSampleTools.configure_rider_sockets(knight)
    ED.save_loaded_asset(skeleton)
    rider_bp=ED.load_asset(B+'/ABP_SampleRider')
    graph=u.AshWellMountedSampleTools.build_animation_graph(rider_bp,ED.load_asset(B+'/A_SampleRider_SeatedIdle'),None,True,u.Vector(-35,-12,35),u.Vector(35,-12,35))
    report['rider_graph']=graph;assert 'errors=0' in graph,graph
    ED.save_loaded_asset(rider_bp)
    blend=ED.load_asset(B+'/BS_SampleHorse_IKSpeed');assert blend
    clips=[ED.load_asset(B+'/HorseRetargetConnected/A_IKSampleHorse_'+n) for n in ['Idle','Walk','Gallop']]
    assert u.AshWellMountedSampleTools.configure_horse_blend_space(blend,*clips)
    ED.save_loaded_asset(blend)
    report['blend_samples']=[{'animation':s.get_editor_property('animation').get_path_name(),'speed':s.get_editor_property('sample_value').x,'rate':s.get_editor_property('rate_scale')} for s in blend.get_editor_property('sample_data')]
    montage=ED.load_asset(B+'/AM_SampleChargeSweep')
    report['montage_seconds']=montage.get_editor_property('sequence_length')
    report['scope']='Existing AnimBPs, Slot, Montage and Notify State retained. Candidate, pending runtime visual review.'
    report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    out=R/'Saved/MountedChargeRound2';out.mkdir(parents=True,exist_ok=True)
    (out/'visual-import.json').write_text(json.dumps(report,indent=2))
    u.log('ROUND2_IMPORT '+json.dumps(report))
    if os.environ.get('ASHWELL_ROUND2_CHAINED')!='1':u.SystemLibrary.quit_editor()
