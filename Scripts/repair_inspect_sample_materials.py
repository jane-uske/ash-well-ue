from pathlib import Path
import unreal as u,json,traceback
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample/';D={}
try:
    for label in ['Knight','Horse']:
        m=u.EditorAssetLibrary.load_asset(B+'SK_Sample'+label);mat=u.EditorAssetLibrary.load_asset(B+'M_Sample'+label)
        # Unreal array iteration returns struct values; write new values back explicitly.
        m.set_editor_property('materials',[u.SkeletalMaterial(material_interface=mat,material_slot_name='Material_0')]);u.EditorAssetLibrary.save_loaded_asset(m)
        D[label]={'bounds':str(m.get_bounds()),'materials':[str(s.material_interface) for s in m.get_editor_property('materials')]}
    for name in ['SM_SamplePoleaxe','SM_SampleShield']:
        D[name]={'bounds':str(u.EditorAssetLibrary.load_asset(B+name).get_bounding_box())}
    for name,bones in [('A_SampleRider_SeatedIdle',['Hips','Head','RightHand','LeftHand','LeftFoot']),('A_SampleHorse_Idle',['Bone_002','Bone_000'])]:
        a=u.EditorAssetLibrary.load_asset(B+name);pose=u.AnimPoseExtensions.get_anim_pose_at_time(a,0,u.AnimPoseEvaluationOptions())
        D[name]={n:{'pose':str(u.AnimPoseExtensions.get_bone_pose(pose,n,u.AnimPoseSpaces.WORLD)),
                   'reference':str(u.AnimPoseExtensions.get_ref_bone_pose(pose,n,u.AnimPoseSpaces.WORLD))} for n in bones}
except Exception:D['error']=traceback.format_exc()
(R/'Saved/MountedChargeStandard/pose-inspection.json').write_text(json.dumps(D,indent=2));u.log('SAMPLE_INSPECT '+json.dumps(D));u.SystemLibrary.quit_editor()
