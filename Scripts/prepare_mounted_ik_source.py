"""Preserve source motion while connecting the original detached IK foot bones.
The CC0 source and the production skeleton are not modified. UE retarget chains
require each end bone to descend from its chain root.
"""
import bpy,json
from mathutils import Matrix
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'SourceAssets/MountedChargeSample/HorseIKSource';D.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'SourceAssets/MountedBoss/MountedHorsePrepared.blend'))
rig=bpy.data.objects['MountedHorseRig'];mesh=bpy.data.objects['SK_Horse'];samples={}
for name in ['Idle','Walk','Gallop']:
    a=bpy.data.actions['A_Horse_'+name];rig.animation_data.action=a
    if a.slots:rig.animation_data.action_slot=a.slots[0]
    poses=[]
    for f in range(round(a.frame_range[1])+1):
        bpy.context.scene.frame_set(f);poses.append({p.name:p.matrix.copy() for p in rig.pose.bones})
    samples[name]=poses
rig.animation_data_clear();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side in ['L','R']:
    for front in [True,False]:
        foot=('IKFrontLeg.' if front else 'IKBackLeg.')+side;parent=('FrontLowerLeg.' if front else 'BackLowerLeg.')+side
        rig.data.edit_bones[foot].parent=rig.data.edit_bones[parent];rig.data.edit_bones[foot].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
def export(name,skin=False):
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    if skin:mesh.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.fbx(filepath=str(D/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},use_space_transform=False,axis_forward='X',axis_up='Z',add_leaf_bones=False,bake_anim=not skin,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE')
export('SK_AlignedSourceHorse',True);report={}
for name,poses in samples.items():
    rig.animation_data_create();action=bpy.data.actions.new('A_AlignedHorse_'+name);action.use_fake_user=True;rig.animation_data.action=action
    bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=len(poses)-1;bpy.context.scene.render.fps=60
    maximum=0
    for f,wanted in enumerate(poses):
        bpy.context.scene.frame_set(f)
        for p in rig.pose.bones:
            pn=p.parent.name if p.parent else None;pr=rest[pn] if pn else Matrix.Identity(4);pp=wanted[pn] if pn else Matrix.Identity(4)
            p.matrix_basis=(pr.inverted()@rest[p.name]).inverted()@pp.inverted()@wanted[p.name];p.rotation_mode='QUATERNION'
            for key in ['location','rotation_quaternion','scale']:p.keyframe_insert(key,frame=f)
        bpy.context.view_layer.update()
        maximum=max(maximum,max((p.matrix.translation-wanted[p.name].translation).length for p in rig.pose.bones))
    export('A_AlignedHorse_'+name);report[name]={'frames':len(poses),'max_world_position_error_cm':maximum}
    assert maximum<.01,report
bpy.ops.wm.save_as_mainfile(filepath=str(D/'ConnectedSource.blend'))
(D/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
