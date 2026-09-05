"""Internal workbench geometry inspection only; this is not a UE render."""
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'ExpeditionFigures.blend'))
bpy.data.objects['SM_Expedition_Companion'].hide_render=True
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(.32,.32,.32)
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.show_shadows=True
scene.display.shading.background_type='WORLD'
scene.world.color=(.07,.07,.07)
bpy.ops.object.camera_add(location=(-3.4,-2.1,2.1))
cam=bpy.context.object
cam.rotation_euler=(Vector((0,-.6,.9))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=2.15
scene.camera=cam
scene.render.resolution_x=840;scene.render.resolution_y=1120;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(root/'qa_geometry_NOT_UE.png')
bpy.ops.render.render(write_still=True)
