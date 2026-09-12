"""Read native retarget settings and actual exported death bone motion."""
import unreal as u,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample/ReferenceProduction';ED=u.EditorAssetLibrary;report={}
for label,bones in [('SourceHorse',['Body','Back','Torso2']),('Horse',['Bone_000','Bone_002'])]:
    clip=ED.load_asset(B+'/A_Reference'+label+'_Death');rows=[]
    for t in [0,.25,.5,1]:
        pose=u.AnimPoseExtensions.get_anim_pose_at_time(clip,t,u.AnimPoseEvaluationOptions())
        row={'time':t}
        for bone in bones:
            p=u.AnimPoseExtensions.get_bone_pose(pose,bone,u.AnimPoseSpaces.WORLD)
            row[bone]={'position':p.translation.to_tuple(),'rotation':p.rotation.rotator().to_tuple()}
        rows.append(row)
    report[label]={'force_root_lock':clip.get_editor_property('force_root_lock'),'enable_root_motion':clip.get_editor_property('enable_root_motion'),'root_motion_root_lock':str(clip.get_editor_property('root_motion_root_lock')),'poses':rows}
retarget=ED.load_asset(B+'/RTG_ReferenceHorse_Death');c=u.IKRetargeterController.get_controller(retarget);ops=[]
for i in range(c.get_num_retarget_ops()):
    op=c.get_op_controller(i);kind=op.get_class().get_name();data={'kind':kind,'enabled':c.get_retarget_op_enabled(i)}
    if 'PelvisMotion' in kind:
        s=op.get_settings()
        data['settings']={k:str(s.get_editor_property(k)) for k in ['source_pelvis_bone','target_pelvis_bone','rotation_alpha','translation_alpha','floor_constraint_weight']}
        for k in ['source_pelvis_bone','target_pelvis_bone']:data['settings'][k]=str(s.get_editor_property(k).get_editor_property('bone_name'))
    ops.append(data)
report['ops']=ops
report['rigs']={}
for label in ['Source','Target']:
    rig=ED.load_asset(B+'/IK_ReferenceDeath'+label);rc=u.IKRigController.get_controller(rig)
    report['rigs'][label]={'pelvis':str(rc.get_retarget_root()),'spine_start':str(rc.get_retarget_chain_start_bone('Spine'))}
(R/'Saved/MountedReferenceProduction/death-native-audit.json').write_text(json.dumps(report,indent=2));u.log('DEATH_AUDIT '+json.dumps(report))
u.EditorPythonScripting.set_keep_python_script_alive(True);finish=time.monotonic()
def quit_ready(dt):
    if time.monotonic()-finish>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(quit_ready)
