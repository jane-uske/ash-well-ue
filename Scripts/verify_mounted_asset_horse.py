"""Verify every baked foot sample against the evaluated source and render a diagnostic.
Run in an isolated background Blender. This is asset QA, not gameplay validation."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parents[1]/'SourceAssets/MountedBoss'
bpy.ops.wm.open_mainfile(filepath=str(O/'MountedHorsePrepared.blend'))
r=bpy.data.objects['MountedHorseRig'];s=bpy.context.scene;j=json.loads((O/'horse_manifest.json').read_text())
checks={}
for label in j['clips']:
 a=bpy.data.actions['A_Horse_'+label];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 errors=[]
 for i in range(j['clips'][label]['frames']):
  s.frame_set(i)
  for name,points in j['clips'][label]['foot_head_positions_cm'].items():errors.append((r.pose.bones[name].head-Vector(points[i])).length)
 checks[label]=max(errors)
print('BAKED_FOOT_MAX_ERROR_CM',checks)
(O/'bake-verification.json').write_text(json.dumps(checks,indent=2))
assert max(checks.values()) < .01, 'Baked horse differs from source by more than 0.01 cm'
r.animation_data.action=bpy.data.actions['A_Horse_Idle'];r.animation_data.action_slot=r.animation_data.action.slots[0];s.frame_set(1)
# Neutral diagnostic studio render, background CLI only.
for ob in list(s.objects):
 if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
for m in bpy.data.materials:
 if m.name in j['materials']:
  m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=j['materials'][m.name]['base_color'];p.inputs['Roughness'].default_value=.68
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0,0,-.7));ground=bpy.context.object
mat=bpy.data.materials.new('DiagnosticGround');mat.diffuse_color=(.055,.06,.065,1);ground.data.materials.append(mat)
for pos,energy,size in [((200,-250,450),800000,350),((-300,200,300),400000,250)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,100))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(460,-650,290));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,108))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=410;s.camera=cam
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=960;s.render.resolution_percentage=100;s.world.color=(.13,.13,.13)
s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG';s.render.filepath=str(O/'horse-neutral-diagnostic.png');bpy.ops.render.render(write_still=True)
