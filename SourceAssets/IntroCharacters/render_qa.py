from pathlib import Path
import bpy,math
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'IntroCharacters.blend'))
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.show_object_outline=False
scene.display.shading.background_type='WORLD';scene.world.color=(.07,.07,.07)
bpy.ops.object.camera_add(location=(-3.1,-3.0,2.0));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,.92))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.18;scene.camera=camera
for role in ['Protagonist','Companion']:
    rig=bpy.data.objects['SK_Intro_'+role+'_Rig'];mesh=bpy.data.objects['SK_Intro_'+role]
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=o!=mesh
    clips=[('Walk',1),('Walk',12),('Walk',22),('Walk',33)]
    if role=='Companion':clips += [('StopSignal',1),('StopSignal',25),('StopSignal',48),('StopSignal',90)]
    for action,frame in clips:
        rig.animation_data.action=bpy.data.actions['A_Intro_'+role+'_'+action]
        scene.frame_set(frame)
        scene.render.filepath=str(OUT/f'QA_{role}_{action}_{frame:03d}_NOT_UE.png')
        bpy.ops.render.render(write_still=True)
print('INTRO_QA_READY')
