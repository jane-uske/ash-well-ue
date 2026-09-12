"""Install one paired action through native UE assets; retain all other moves."""
import unreal as u,json,traceback,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';D=B+'/ReferenceProduction'
ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();report={}
try:
    ED.make_directory(D);u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    clips={};horse=ED.load_asset(B+'/SK_SampleHorse');rider=ED.load_asset(B+'/SK_SampleKnight')
    for name,skin in [('A_ReferenceRider_SeatedIdle',rider),('A_ReferenceRider_Death',rider),('A_ReferenceRider_ChargeSweep',rider),('A_ReferenceHorse_ChargeSweep',horse)]:
        opt=u.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_as_skeletal':True,'import_mesh':False,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
        opt.skeleton=skin.get_editor_property('skeleton');data=opt.anim_sequence_import_data
        for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_default_sample_rate':False,'custom_sample_rate':60}.items():data.set_editor_property(k,v)
        t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedReferenceProduction/Animation'/(name+'.fbx'));t.destination_path=D;t.destination_name=name
        t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
        clip=ED.load_asset(D+'/'+name);assert clip;clips[name]=clip;report[name]=clip.get_editor_property('sequence_length')
    timing=json.loads((R/'SourceAssets/MountedReferenceProduction/charge-timing.json').read_text())
    definition=u.MountedAuthoredAction()
    for k,v in timing['phase_seconds'].items():definition.set_editor_property('pass' if k=='pass_time' else k,v)
    curve=u.AshWellMountedSampleTools.build_distance_curve(D+'/C_ChargeForwardDistance',[u.Vector2D(*p) for p in timing['distance_samples_cm']]);assert curve;ED.save_loaded_asset(curve);definition.set_editor_property('forward_distance',curve)
    # Measured height gates are authored into the horse sequence for the native solver.
    clip=clips['A_ReferenceHorse_ChargeSweep'];duration=clip.get_editor_property('sequence_length');times=[min(f/60,duration) for f in range(round(duration*60)+1)]
    feet={'ContactGateFL':'Bone_052','ContactGateFR':'Bone_046','ContactGateBL':'Bone_031','ContactGateBR':'Bone_025'}
    points={n:[] for n in feet}
    for t in times:
        pose=u.AnimPoseExtensions.get_anim_pose_at_time(clip,t,u.AnimPoseEvaluationOptions())
        for n,b in feet.items():points[n].append(u.AnimPoseExtensions.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation.z)
    for name,heights in points.items():
        values=[0.0 if z<min(heights[max(0,i-21):min(len(heights),i+22)])+3.5 else 1000.0 for i,z in enumerate(heights)]
        u.AnimationLibrary.remove_curve(clip,name,False);u.AnimationLibrary.add_curve(clip,name,u.RawCurveTrackTypes.RCT_FLOAT,False);u.AnimationLibrary.add_float_curve_keys(clip,name,times,values)
    u.AnimationLibrary.remove_curve(clip,'AuthoredFootLock',False);u.AnimationLibrary.add_curve(clip,'AuthoredFootLock',u.RawCurveTrackTypes.RCT_FLOAT,False);u.AnimationLibrary.add_float_curve_keys(clip,'AuthoredFootLock',[0.,duration],[1.,1.])
    ED.save_loaded_asset(clip)
    horse_bp=ED.load_asset(B+'/FootContactCandidate/ABP_SampleHorse_Planted')
    horse_graph=u.AshWellMountedSampleTools.build_animation_graph(horse_bp,ED.load_asset(B+'/FootContactCandidate/A_ContactHorse_Idle'),ED.load_asset(B+'/FootContactCandidate/BS_ContactHorse_Speed'),False,u.Vector(),u.Vector(),True)
    assert 'errors=0' in horse_graph;ED.save_loaded_asset(horse_bp);report['horse_graph']=horse_graph
    horse_m=u.AshWellMountedSampleTools.build_reference_montage(clip,D+'/AM_ReferenceHorse_ChargeSweep',definition,False);assert horse_m;ED.save_loaded_asset(horse_m);definition.set_editor_property('horse_montage',horse_m)
    rider_m=u.AshWellMountedSampleTools.build_reference_montage(clips['A_ReferenceRider_ChargeSweep'],D+'/AM_ReferenceRider_ChargeSweep',definition,True);assert rider_m;ED.save_loaded_asset(rider_m)
    source_horse=ED.load_asset(B+'/HorseRetargetConnected/SK_AlignedSourceHorse')
    opt=u.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_as_skeletal':True,'import_mesh':False,'import_animations':True,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
    opt.skeleton=source_horse.get_editor_property('skeleton');di=opt.anim_sequence_import_data
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'use_default_sample_rate':False,'custom_sample_rate':60}.items():di.set_editor_property(k,v)
    task=u.AssetImportTask();task.filename=str(R/'SourceAssets/MountedReferenceProduction/HorseDeathSource/A_AlignedHorse_Death.fbx');task.destination_path=D;task.destination_name='A_ReferenceSourceHorse_Death';task.automated=True;task.save=True;task.replace_existing=True;task.replace_existing_settings=True;task.options=opt;task.factory=u.FbxFactory();AT.import_asset_tasks([task])
    src=ED.load_asset(D+'/A_ReferenceSourceHorse_Death');assert src
    retarget=ED.load_asset(D+'/RTG_ReferenceHorse_Death') or ED.duplicate_asset(B+'/HorseRetargetConnected/RTG_SampleHorse',D+'/RTG_ReferenceHorse_Death');assert retarget
    controller=u.IKRetargeterController.get_controller(retarget)
    for i in range(controller.get_num_retarget_ops()):
        kind=controller.get_op_controller(i).get_class().get_name()
        if any(n in kind for n in ['FloorConstraint','RunIKRig','RootMotion']):controller.set_retarget_op_enabled(i,False)
    ED.save_loaded_asset(retarget)
    args=u.IKRetargetBatchOperationInputs();args.assets_to_retarget=[ED.find_asset_data(src.get_path_name())];args.source_mesh=source_horse;args.target_mesh=horse;args.ik_retarget_asset=retarget;args.search='A_ReferenceSourceHorse_';args.replace='A_ReferenceHorse_';args.target_path=D;args.include_referenced_assets=False;args.overwrite_existing_files=True
    result=u.IKRetargetBatchOperation.run_batch_retarget(args);assert len(result)==1
    horse_death=result[0].get_asset();ED.save_loaded_asset(horse_death)
    death_definition=u.MountedAuthoredAction();death_definition.set_editor_property('end',horse_death.get_editor_property('sequence_length'))
    horse_dead_m=u.AshWellMountedSampleTools.build_reference_montage(horse_death,D+'/AM_ReferenceHorse_Death',death_definition,False);assert horse_dead_m;ED.save_loaded_asset(horse_dead_m)
    death_definition.set_editor_property('end',2.8)
    rider_dead_m=u.AshWellMountedSampleTools.build_reference_montage(clips['A_ReferenceRider_Death'],D+'/AM_ReferenceRider_Death',death_definition,False);assert rider_dead_m;ED.save_loaded_asset(rider_dead_m)
    actions=ED.load_asset(B+'/DA_MountedSampleActions');moves=dict(actions.montages);moves['charge']=rider_m;actions.set_editor_property('montages',moves)
    defs=dict(actions.authored_actions);defs['charge']=definition;actions.set_editor_property('authored_actions',defs);actions.set_editor_property('rider_death',rider_dead_m);actions.set_editor_property('horse_death',horse_dead_m);ED.save_loaded_asset(actions)
    bp=ED.load_asset(B+'/ABP_SampleRider');graph=u.AshWellMountedSampleTools.build_animation_graph(bp,clips['A_ReferenceRider_SeatedIdle'],None,True,u.Vector(-35,-12,35),u.Vector(35,-12,35));assert 'errors=0' in graph;ED.save_loaded_asset(bp)
    u.AshWellReferenceEnvironmentTools.finish_asset_compilation()
    report.update(passed=True,graph=graph,paired_montages=[rider_m.get_path_name(),horse_m.get_path_name()],curve=curve.get_path_name(),definition=timing['phase_seconds'],scope='Only charge registry migrated; other attacks untouched. Needs runtime/dynamic acceptance.')
except Exception:
    report.update(passed=False,error=traceback.format_exc());u.log_error(report['error'])
finally:
    (R/'Saved/MountedReferenceProduction/animation-import.json').write_text(json.dumps(report,indent=2));u.log('REFERENCE_ANIMATION_IMPORT '+json.dumps(report))
    if __import__('os').environ.get('ASHWELL_REFERENCE_CHAINED')!='1':
        u.EditorPythonScripting.set_keep_python_script_alive(True);finish=time.monotonic()
        def quit_ready(dt):
            if time.monotonic()-finish>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
        handle=u.register_slate_post_tick_callback(quit_ready)
