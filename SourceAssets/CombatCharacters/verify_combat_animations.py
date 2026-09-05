from pathlib import Path
import bpy,json,math
from mathutils import Vector

OUT=Path(__file__).resolve().parent
manifest=json.loads((OUT/'manifest.json').read_text())
checks=[]
for clip in manifest['animations']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(OUT/clip['file']),use_anim=True)
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    assert len(rigs)==1,clip['file']
    rig=rigs[0]
    assert set(b.name for b in rig.data.bones)==set(manifest['bones']),clip['file']
    action=rig.animation_data.action
    start,end=map(float,action.frame_range)
    fps=bpy.context.scene.render.fps
    assert abs((end-start)/fps-clip['duration_seconds'])<.0001,(clip['name'],start,end,fps)
    roots=[];hand=[];hip=[];states=[]
    for frame in range(round(start),round(end)+1):
        bpy.context.scene.frame_set(frame)
        roots.append(rig.pose.bones['root'].matrix.copy())
        hand.append(tuple(rig.pose.bones['hand_L'].head))
        hip.append(tuple(rig.pose.bones['pelvis'].head))
        states.append({b.name:b.matrix.copy() for b in rig.pose.bones})
        assert all(math.isfinite(v) for b in rig.pose.bones for row in b.matrix for v in row)
    drift=max((r.translation-roots[0].translation).length for r in roots)
    rootrot=max(r.to_quaternion().rotation_difference(roots[0].to_quaternion()).angle for r in roots)
    assert drift<1e-5 and rootrot<1e-4,(clip['name'],drift,rootrot)
    loop_error=max((states[0][b].translation-states[-1][b].translation).length for b in states[0])
    if clip['loop']:assert loop_error<1e-4,(clip['name'],loop_error)
    checks.append({'clip':clip['name'],'frames':[start,end],'fps':fps,'duration':(end-start)/fps,
                   'bones':len(rig.data.bones),'root_drift_m':drift,'root_rotation_drift_rad':rootrot,
                   'endpoints_bone_position_error_m':loop_error,
                   'left_hand_travel_span_m':max((Vector(p)-Vector(hand[0])).length for p in hand),
                   'minimum_pelvis_height_m':min(p[2] for p in hip)})
(OUT/'verification.json').write_text(json.dumps({'status':'PASS','verification_scope':'Blender FBX round trip; not an Unreal runtime check','checks':checks},indent=2)+'\n')
print('COMBAT_ANIMATION_FBX_VERIFICATION_PASS')

bpy.ops.wm.open_mainfile(filepath=str(OUT/'CombatAnimations.blend'))
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=720;scene.render.resolution_y=720
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
scene.world.color=(.065,.065,.065)
rig=bpy.data.objects['SK_Intro_Protagonist_Rig'];mesh=bpy.data.objects['SK_Intro_Protagonist']
for o in scene.objects:
    if o.type=='MESH':o.hide_render=o!=mesh
bpy.ops.object.camera_add(location=(3.0,-4.0,2.0));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,.86))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.25;scene.camera=camera
renders=[]
for mode,frame in [('Attack',1),('Attack',19),('Attack',25),('Attack',34),('Dodge',13),('Death',79),('CombatWalk',1),('CombatWalk',10),('Hit',6)]:
    rig.animation_data.action=bpy.data.actions['A_Combat_Protagonist_'+mode]
    scene.frame_set(frame)
    path=OUT/f'QA_{mode}_{frame:03d}_NOT_UE.png'
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points=[evaluated.matrix_world@v.co for v in evaluated.data.vertices]
    bounds=[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
    renders.append({'mode':mode,'frame':frame,'image':path.name,'deformed_mesh_bounds_m':bounds})
(OUT/'pose-review.json').write_text(json.dumps(renders,indent=2)+'\n')
print('COMBAT_ANIMATION_QA_RENDER_READY')
