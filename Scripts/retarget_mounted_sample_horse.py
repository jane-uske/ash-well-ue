"""Create UE IK Rigs, an editable IK Retargeter and isolated gait candidates.
No original source mesh, animation or active BlendSpace is overwritten.
"""
from pathlib import Path
import unreal as u,json,traceback
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';D=B+'/HorseRetargetConnected'
ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();report={}
try:
    ED.make_directory(D);u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    def aligned_import(name,source,skeleton=None):
        if ED.does_asset_exist(D+'/'+name):return ED.load_asset(D+'/'+name)
        opt=u.FbxImportUI();anim=skeleton is not None
        for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION if anim else u.FBXImportType.FBXIT_SKELETAL_MESH,'import_as_skeletal':True,'import_mesh':not anim,'import_animations':anim,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
        if anim:opt.skeleton=skeleton
        data=opt.anim_sequence_import_data if anim else opt.skeletal_mesh_import_data
        data.set_editor_property('convert_scene',True);data.set_editor_property('convert_scene_unit',True)
        if anim:data.set_editor_property('use_default_sample_rate',False);data.set_editor_property('custom_sample_rate',60)
        t=u.AssetImportTask();t.filename=str(R/'SourceAssets/MountedChargeSample/HorseIKSource'/(name+'.fbx'));t.destination_path=D;t.destination_name=name;t.automated=True;t.save=True;t.options=opt;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);a=ED.load_asset(D+'/'+name);assert a,name
        if not anim:ED.save_loaded_asset(a.get_editor_property('skeleton'))
        return a
    source=aligned_import('SK_AlignedSourceHorse','SK_Horse');target=ED.load_asset(B+'/SK_SampleHorse')
    clips=[aligned_import('A_AlignedHorse_'+n,'A_Horse_'+n,source.get_editor_property('skeleton')) for n in ['Idle','Walk','Gallop']]
    chains=[('Spine','Back','Torso3','Bone_000','Bone_016'),('Neck','Neck1','Head','Bone_015','Bone_045'),('Tail','Tail1','Tail5','Bone_014','Bone_010'),('FrontR','FrontUpperLeg.R','FF.R','Bone_051','Bone_046'),('FrontL','FrontUpperLeg.L','FF.L','Bone_057','Bone_052'),('BackR','BackLeg.R','FFB.R','Bone_030','Bone_025'),('BackL','BackLeg.L','FFB.L','Bone_036','Bone_031')]
    rigs=[]
    for label,mesh,root,is_target in [('Source',source,'Back',False),('Target',target,'Bone_000',True)]:
        name='IK_SampleHorse'+label;a=ED.load_asset(D+'/'+name) or AT.create_asset(name,D,u.IKRigDefinition,u.IKRigDefinitionFactory());c=u.IKRigController.get_controller(a);assert c.set_skeletal_mesh(mesh);assert c.set_retarget_root(root)
        # Script owns these isolated rigs; reset only their setup on a rerun.
        for ch in c.get_retarget_chains():c.remove_retarget_chain(ch.chain_name)
        for goal in list(c.get_all_goals()):c.remove_goal(goal.goal_name)
        for i in reversed(range(c.get_num_solvers())):c.remove_solver(i)
        for name,ss,se,ts,te in chains:
            start,end=(ts,te) if is_target else (ss.replace('.','_'),se.replace('.','_'));leg=name.startswith(('Front','Back'));goal='Goal_'+name if leg else 'None'
            if leg:
                made=c.add_new_goal(goal,end);assert str(made)==goal,(label,goal,end,str(made))
                if is_target:
                    solver=c.add_solver('/Script/IKRig.IKRigLimbSolver');assert solver>=0
                    assert c.set_start_bone(start,solver);assert c.connect_goal_to_solver(goal,solver)
            assert str(c.add_retarget_chain(name,start,end,goal))==name,name
        ED.save_loaded_asset(a);rigs.append(a)
    name='RTG_SampleHorse';a=ED.load_asset(D+'/'+name) or AT.create_asset(name,D,u.IKRetargeter,u.IKRetargetFactory());c=u.IKRetargeterController.get_controller(a)
    c.set_ik_rig(u.RetargetSourceOrTarget.SOURCE,rigs[0]);c.set_ik_rig(u.RetargetSourceOrTarget.TARGET,rigs[1]);c.remove_all_ops();c.add_default_ops()
    for name,*_ in chains:assert c.set_source_chain(name,name)
    ops=[(i,c.get_op_name(i),c.get_op_controller(i)) for i in range(c.get_num_retarget_ops())]
    report['ops_before_floor']=[(i,str(n),x.get_class().get_name()) for i,n,x in ops]
    run=next((i,n,x) for i,n,x in ops if 'RunIKRig' in x.get_class().get_name())
    for i,n,x in ops:
        if 'RootMotion' in x.get_class().get_name():c.set_retarget_op_enabled(i,False)
    floor_index=c.add_retarget_op('/Script/IKRig.IKRetargetFloorConstraintOp');assert floor_index>=0
    assert c.set_parent_op_by_name(c.get_op_name(floor_index),run[1]);floor_index=c.get_index_of_op_by_name(c.get_op_name(floor_index))
    floor=next(c.get_op_controller(i) for i in range(c.get_num_retarget_ops()) if 'FloorConstraint' in c.get_op_controller(i).get_class().get_name())
    settings=floor.get_settings();items=list(settings.chains_to_affect)
    for item in items:
        item.enable_floor_constraint=str(item.target_chain_name).startswith(('Front','Back'));item.maintain_height_offset=1.0
        if item.enable_floor_constraint:
            item.use_foot=True
            foot=item.foot;foot.medial_offset=3;foot.lateral_offset=3;foot.heel_offset=5;foot.toe_offset=5;foot.vertical_offset=0;item.foot=foot
    assert sum(x.enable_floor_constraint for x in items)==4,'floor constraint did not bind all four legs'
    settings.chains_to_affect=items;floor.set_settings(settings);ED.save_loaded_asset(a)
    report['ops']=[(i,str(c.get_op_name(i)),c.get_op_controller(i).get_class().get_name()) for i in range(c.get_num_retarget_ops())]
    args=u.IKRetargetBatchOperationInputs();args.assets_to_retarget=[ED.find_asset_data(x.get_path_name()) for x in clips];args.source_mesh=source;args.target_mesh=target;args.ik_retarget_asset=a;args.search='A_AlignedHorse_';args.replace='A_IKSampleHorse_';args.target_path=D;args.include_referenced_assets=False;args.overwrite_existing_files=True
    result=u.IKRetargetBatchOperation.run_batch_retarget(args);report['outputs']=[str(x.package_name) for x in result];assert len(result)==3,report
    for d in result:ED.save_loaded_asset(d.get_asset())
    report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    (R/'Saved/MountedChargeStandard/ue-horse-retarget.json').write_text(json.dumps(report,indent=2));u.log('HORSE_IK_RETARGET '+json.dumps(report));u.SystemLibrary.quit_editor()
