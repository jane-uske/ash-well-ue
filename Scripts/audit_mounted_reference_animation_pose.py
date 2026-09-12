import unreal as u,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/Combat/MountedChargeSample/ReferenceProduction';clip=u.EditorAssetLibrary.load_asset(B+'/A_ReferenceHorse_ChargeSweep');rows=[]
for f in range(349):
 pose=u.AnimPoseExtensions.get_anim_pose_at_time(clip,min(f/60,clip.get_editor_property('sequence_length')),u.AnimPoseEvaluationOptions())
 points={}
 for n in ['Bone_000','Bone_053','Bone_047','Bone_032','Bone_026']:
  p=u.AnimPoseExtensions.get_bone_pose(pose,n,u.AnimPoseSpaces.WORLD).translation
  points[n]=[-p.y,p.x,p.z]
 rows.append(points)
(R/'Saved/MountedReferenceProduction/imported-horse-pose.json').write_text(json.dumps(rows));u.log('IMPORTED_HORSE_POSE_READY')
u.EditorPythonScripting.set_keep_python_script_alive(True);finish=time.monotonic()
def quit_ready(dt):
 if time.monotonic()-finish>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(quit_ready)
