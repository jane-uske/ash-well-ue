"""Build a real UE Foot Placement -> Leg IK candidate for the four horse limbs.

Original retarget clips are retained. New curves describe intended contact phases,
not measured physical foot speeds. Runtime planting is performed by UE nodes.
Enable only with -MountedFootPlacement until dynamic review is complete.
"""
from pathlib import Path
import unreal as u,json,traceback
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample';D=B+'/FootContactCandidate'
ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();report={}
try:
    horse=ED.load_asset(B+'/SK_SampleHorse');skeleton=horse.get_editor_property('skeleton')
    assert u.AshWellMountedSampleTools.configure_horse_contact_bones(horse)
    ED.save_loaded_asset(skeleton);ED.make_directory(D)
    clips=[]
    for label in ['Idle','Walk','Gallop']:
        src=ED.load_asset(B+'/HorseRetargetConnected/A_IKSampleHorse_'+label)
        name='A_ContactHorse_'+label;dest=D+'/'+name
        clip=ED.load_asset(dest) if ED.does_asset_exist(dest) else ED.duplicate_asset(src.get_path_name().split('.')[0],dest)
        assert clip;clips.append(clip)
        duration=clip.get_editor_property('sequence_length');times=[min(f/60,duration) for f in range(round(duration*60)+1)]
        feet={'ContactGateFL':'Bone_052','ContactGateFR':'Bone_046','ContactGateBL':'Bone_031','ContactGateBR':'Bone_025'}
        points={n:[] for n in feet}
        for t in times:
            pose=u.AnimPoseExtensions.get_anim_pose_at_time(src,t,u.AnimPoseEvaluationOptions())
            for n,bone in feet.items():points[n].append(u.AnimPoseExtensions.get_bone_pose(pose,bone,u.AnimPoseSpaces.WORLD).translation.z)
        entry={}
        for name,heights in points.items():
            floor=min(heights);values=[0.0 if z<floor+4.0 else 1000.0 for z in heights]
            u.AnimationLibrary.remove_curve(clip,name,False)
            u.AnimationLibrary.add_curve(clip,name,u.RawCurveTrackTypes.RCT_FLOAT,False)
            u.AnimationLibrary.add_float_curve_keys(clip,name,times,values)
            entry[name]={'keys':len(values),'contact_keys':values.count(0.0),'min_source_z_cm':floor}
        ED.save_loaded_asset(clip);report[label]=entry
    blend=ED.load_asset(D+'/BS_ContactHorse_Speed') if ED.does_asset_exist(D+'/BS_ContactHorse_Speed') else None
    if not blend:
        factory=u.BlendSpaceFactory1D();factory.set_editor_property('target_skeleton',skeleton)
        blend=AT.create_asset('BS_ContactHorse_Speed',D,u.BlendSpace1D,factory)
    assert u.AshWellMountedSampleTools.configure_horse_blend_space(blend,*clips);ED.save_loaded_asset(blend)
    name='ABP_SampleHorse_Planted'
    bp=ED.load_asset(D+'/'+name) if ED.does_asset_exist(D+'/'+name) else None
    if not bp:
        factory=u.AnimBlueprintFactory();factory.set_editor_property('target_skeleton',skeleton)
        factory.set_editor_property('preview_skeletal_mesh',horse);factory.set_editor_property('parent_class',u.AshWellMountedSampleAnimInstance)
        bp=AT.create_asset(name,D,u.AnimBlueprint,factory)
    result=u.AshWellMountedSampleTools.build_animation_graph(bp,clips[0],blend,False,u.Vector(),u.Vector(),True)
    report['graph']=result;assert 'errors=0' in result,result;ED.save_loaded_asset(bp)
    report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    (R/'Saved/MountedChargeRound2/foot-contact-build.json').write_text(json.dumps(report,indent=2))
    u.log('FOOT_CONTACT_CANDIDATE '+json.dumps(report));u.SystemLibrary.quit_editor()
