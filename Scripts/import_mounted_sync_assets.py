"""Install recorded SoundCue graphs and the larger horse's contact animation."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();report={}
try:
    A=B+'/Audio';ED.make_directory(A)
    manifest=json.loads((R/'SourceAssets/MountedReferenceProduction/Audio/audio-manifest.json').read_text());waves={}
    for item in manifest['files']:
        name=item['name'];t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedReferenceProduction/Audio/Prepared'/(name+'.wav'));t.destination_path=A;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
        AT.import_asset_tasks([t]);waves[name]=ED.load_asset(A+'/'+name);assert waves[name]
    report['cues']={}
    for name,variants in manifest['cues'].items():
        with u.ScopedEditorTransaction('Author mounted combat sound'):
            cue=u.AshWellMountedSampleTools.build_combat_sound_cue(A+'/'+name,[waves[v] for v in variants],1.0);assert cue
        ED.save_loaded_asset(cue);report['cues'][name]={'path':cue.get_path_name(),'variants':variants}
    D=B+'/ReferenceProduction';name='A_ReferenceHorse_ChargeSweep'
    timing=json.loads((R/'SourceAssets/MountedReferenceProduction/charge-timing.json').read_text())
    curve=u.AshWellMountedSampleTools.build_distance_curve(D+'/C_ChargeForwardDistance',[u.Vector2D(*p) for p in timing['distance_samples_cm']]);assert curve;ED.save_loaded_asset(curve)
    assert abs(curve.get_float_value(5.8)-timing['distance_samples_cm'][-1][1])<.01
    report['forward_distance_cm']=curve.get_float_value(5.8)
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    opt=u.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_as_skeletal':True,'import_mesh':False,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
    opt.skeleton=ED.load_asset(B+'/SK_SampleHorse').get_editor_property('skeleton')
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_default_sample_rate':False,'custom_sample_rate':60}.items():opt.anim_sequence_import_data.set_editor_property(k,v)
    t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedReferenceProduction/AssemblyRevision'/(name+'.fbx'));t.destination_path=D;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
    clip=ED.load_asset(D+'/'+name);assert abs(clip.get_editor_property('sequence_length')-5.8)<.001
    times=[f/60 for f in range(349)];points={n:[] for n in ['ContactGateFL','ContactGateFR','ContactGateBL','ContactGateBR']}
    for t in times:
        pose=u.AnimPoseExtensions.get_anim_pose_at_time(clip,t,u.AnimPoseEvaluationOptions())
        for n,b in zip(points,['Bone_052','Bone_046','Bone_031','Bone_025']):points[n].append(u.AnimPoseExtensions.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation.z)
    for name,heights in points.items():
        values=[0.0 if z<min(heights[max(0,i-21):min(len(heights),i+22)])+3.5 else 1000.0 for i,z in enumerate(heights)]
        u.AnimationLibrary.remove_curve(clip,name,False);u.AnimationLibrary.add_curve(clip,name,u.RawCurveTrackTypes.RCT_FLOAT,False);u.AnimationLibrary.add_float_curve_keys(clip,name,times,values)
    u.AnimationLibrary.remove_curve(clip,'AuthoredFootLock',False);u.AnimationLibrary.add_curve(clip,'AuthoredFootLock',u.RawCurveTrackTypes.RCT_FLOAT,False);u.AnimationLibrary.add_float_curve_keys(clip,'AuthoredFootLock',[0.,5.8],[1.,1.])
    ED.save_loaded_asset(clip);u.AshWellReferenceEnvironmentTools.finish_asset_compilation();report.update(passed=True,horse=clip.get_path_name(),horse_world_scale=1.69,rider_charge_unchanged=True)
except Exception:report.update(passed=False,error=traceback.format_exc());u.log_error(report['error'])
(R/'Saved/MountedReferenceProduction/sync-import.json').write_text(json.dumps(report,indent=2)+'\n');u.log('MOUNTED_SYNC_IMPORT '+json.dumps(report))
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.monotonic()
def finish(dt):
    if time.monotonic()-started>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
