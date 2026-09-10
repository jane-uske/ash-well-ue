"""Run in the MCP Blender session after importing the Quaternius Standard GLB."""
from pathlib import Path
import bpy, json, math
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'SourceAssets/AnimationTrial'
rig=bpy.data.objects['Rig']
mesh=bpy.data.objects['Mannequin']
collection=bpy.data.collections['AW_CommunityAnimation_Trial']
assert not bpy.data.objects.get('AW_TrialHammer'), 'Trial already prepared'
for track in rig.animation_data.nla_tracks: track.mute=True
rig.animation_data.action=None
for bone in rig.pose.bones: bone.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()

# A simple test prop, explicitly not the approved Warden weapon design.
steel=bpy.data.materials.new('AW_TrialHammerSteel');steel.diffuse_color=(.12,.15,.18,1)
parts=[]
hand=rig.data.bones['DEF-hand.R'].matrix_local.copy()
for name,center,scale in [('Handle',(.17,.025,0),(.70,.035,.035)),('Head',(.52,.025,0),(.20,.33,.19))]:
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj=bpy.context.object;obj.name='AW_TrialHammer_'+name
    for v in obj.data.vertices: v.co=hand @ (Vector(center)+Vector((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2])))
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection.objects.link(obj);obj.data.materials.append(steel)
    group=obj.vertex_groups.new(name='DEF-hand.R');group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    obj.parent=rig;mod=obj.modifiers.new('Hand bone','ARMATURE');mod.object=rig
    bevel=obj.modifiers.new('Soft test-prop edges','BEVEL');bevel.width=.01;bevel.segments=2
    parts.append(obj)
parts[0].name='AW_TrialHammer'

def select_export():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [rig,mesh]+parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig

def export(name,animated):
    select_export()
    bpy.ops.export_scene.fbx(filepath=str(OUT/name),use_selection=True,object_types={'ARMATURE','MESH'},
        add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        bake_anim=animated,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,bake_anim_step=1,path_mode='AUTO')

export('SK_TrialMannequin.fbx',False)
scene=bpy.context.scene
scene.render.fps=24;scene.frame_start=0;scene.frame_end=37
rig.animation_data.action=bpy.data.actions['Sword_Attack']
rig.animation_data.action_slot=rig.animation_data.action.slots[0]
export('A_Trial_SourceSlash.fbx',True)
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CommunityAnimationTrial.blend'))
(OUT/'preparation.json').write_text(json.dumps({'source':'Quaternius Universal Animation Library Standard',
    'source_clip':'Sword_Attack','source_duration_seconds':36.8/24,'export_duration_seconds':37/24,
    'fps':24,'bones':len(rig.data.bones),'weapon_bone':'DEF-hand.R',
    'note':'Sword slash repurposing experiment; not authored hammer motion or Warden retarget.'},indent=2))
result={'prepared':True,'files':['SK_TrialMannequin.fbx','A_Trial_SourceSlash.fbx'],'bones':len(rig.data.bones)}
