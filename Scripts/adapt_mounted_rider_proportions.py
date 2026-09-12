"""Bake a larger rider's charge grip with Blender native IK; retain source assets."""
import bpy,json
from pathlib import Path
from mathutils import Matrix

R=Path(__file__).resolve().parents[1]
O=R/'SourceAssets/MountedReferenceProduction/ProportionRevision';O.mkdir(parents=True,exist_ok=True)
old_scale,new_scale=1.35,1.60
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceAssets/MountedReferenceProduction/Animation/RiderAuthored.blend'))
rig=bpy.data.objects['SampleKnightRig'];scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['A_ReferenceRider_ChargeSweep']
pivot=rig.data.bones['Hips'].matrix_local.translation.copy()
samples=[]
for frame in range(349):
    scene.frame_set(frame);bpy.context.view_layer.update()
    hand=rig.pose.bones['RightHand'].matrix.copy()
    hand.translation=pivot+(hand.translation-pivot)*(old_scale/new_scale)
    samples.append(rig.matrix_world@hand)
target=bpy.data.objects.new('ChargeGripWorldPath',None);scene.collection.objects.link(target)
target.rotation_mode='QUATERNION'
for frame,matrix in enumerate(samples):
    target.matrix_world=matrix
    target.keyframe_insert('location',frame=frame);target.keyframe_insert('rotation_quaternion',frame=frame)
ik=rig.pose.bones['RightForeArm'].constraints.new('IK');ik.name='Larger rider preserves charge grip'
ik.target=target;ik.chain_count=2;ik.use_stretch=False;ik.iterations=64
rotation=rig.pose.bones['RightHand'].constraints.new('COPY_ROTATION');rotation.name='Preserve authored blade direction'
rotation.target=target;rotation.target_space='WORLD';rotation.owner_space='WORLD'
errors=[]
for frame,matrix in enumerate(samples):
    scene.frame_set(frame);bpy.context.view_layer.update()
    evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    errors.append(((evaluated.matrix_world@evaluated.pose.bones['RightHand'].matrix).translation-matrix.translation).length*new_scale)
assert max(errors)<.5,('Native IK did not preserve grip',max(errors))
scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderGripConstraints.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.nla.bake(frame_start=0,frame_end=348,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
rig.animation_data.action.name='A_ReferenceRider_ChargeSweep_Proportions'
scene.frame_start=0;scene.frame_end=348;scene.render.fps=60;scene.frame_set(0)
bpy.ops.export_scene.fbx(filepath=str(O/'A_ReferenceRider_ChargeSweep.fbx'),use_selection=True,object_types={'ARMATURE'},use_space_transform=False,axis_forward='X',axis_up='Z',add_leaf_bones=False,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'RiderGripBaked.blend'))
(O/'grip-adaptation.json').write_text(json.dumps({'source':'Animation/RiderAuthored.blend','source_rider_scale':old_scale,'target_rider_scale':new_scale,'frames':349,'seconds':5.8,'method':'Blender native two-bone IK and Copy Rotation, visually baked to FBX for existing UE Montage','maximum_grip_world_error_cm':max(errors),'weapon_size_or_sweep_radius_changed':False,'scope':'charge right arm only; original animation and model files untouched'},indent=2)+'\n')
print('RIDER_GRIP_ADAPTED',max(errors),flush=True)
