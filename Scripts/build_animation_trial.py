"""Create an isolated, looping community-animation comparison scene in UE."""
from pathlib import Path
import unreal as u, json
ROOT=Path(__file__).resolve().parents[1]
BASE='/Game/AshWell/AnimationTrial'
SRC=ROOT/'SourceAssets/AnimationTrial'
ed=u.EditorAssetLibrary; tools=u.AssetToolsHelpers.get_asset_tools()
def asset_import(filename,name,skeleton=None):
    opts=u.FbxImportUI()
    for key,value in dict(import_mesh=skeleton is None,import_as_skeletal=True,import_materials=False,
        import_textures=False,import_animations=skeleton is not None,create_physics_asset=False,
        automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION if skeleton else u.FBXImportType.FBXIT_SKELETAL_MESH).items():
        opts.set_editor_property(key,value)
    if skeleton:opts.skeleton=skeleton
    data=opts.anim_sequence_import_data if skeleton else opts.skeletal_mesh_import_data
    for key,value in dict(convert_scene=True,convert_scene_unit=True,force_front_x_axis=False,import_uniform_scale=1.).items():data.set_editor_property(key,value)
    if skeleton:
        data.set_editor_property('use_default_sample_rate',False)
        data.set_editor_property('custom_sample_rate',24)
    task=u.AssetImportTask();task.filename=str(SRC/filename);task.destination_path=BASE
    task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True
    task.options=opts;task.factory=u.FbxFactory();tools.import_asset_tasks([task])
    result=ed.load_asset(BASE+'/'+name)
    if not result:
        result=next((ed.load_asset(p) for p in task.imported_object_paths if isinstance(ed.load_asset(p),u.AnimSequence)),None)
        assert result,list(task.imported_object_paths)
        ed.rename_asset(result.get_path_name(),BASE+'/'+name);result=ed.load_asset(BASE+'/'+name)
    return result

mesh=ed.load_asset(BASE+'/SK_TrialMannequin') or asset_import('SK_TrialMannequin.fbx','SK_TrialMannequin')
assert isinstance(mesh,u.SkeletalMesh)
if not mesh.skeleton:
    # Only the disposable trial assets: recover from an unsaved generated skeleton.
    for path in ['/A_Trial_SourceSlash','/SK_TrialMannequin']:
        if ed.does_asset_exist(BASE+path):
            try:assert ed.delete_asset(BASE+path)
            except RuntimeError:
                # Loading a broken animation can log an exception after deletion.
                assert not ed.does_asset_exist(BASE+path)
    mesh=asset_import('SK_TrialMannequin.fbx','SK_TrialMannequin')
assert isinstance(mesh.skeleton,u.Skeleton)
assert ed.save_loaded_asset(mesh.skeleton)
anim=ed.load_asset(BASE+'/A_Trial_SourceSlash') or asset_import('A_Trial_SourceSlash.fbx','A_Trial_SourceSlash',mesh.skeleton)
assert isinstance(anim,u.AnimSequence)
assert anim.get_editor_property('skeleton')==mesh.skeleton
anim.set_editor_property('enable_root_motion',False)

def material(name,color,metal=0):
    mat=ed.load_asset(BASE+'/'+name) or tools.create_asset(name,BASE,u.Material,u.MaterialFactoryNew())
    m=u.MaterialEditingLibrary;m.delete_all_material_expressions(mat)
    c=m.create_material_expression(mat,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(*color,1)
    m.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    for value,prop in [(metal,u.MaterialProperty.MP_METALLIC),(.55,u.MaterialProperty.MP_ROUGHNESS)]:
        x=m.create_material_expression(mat,u.MaterialExpressionConstant);x.r=value;m.connect_material_property(x,'',prop)
    m.recompile_material(mat);ed.save_loaded_asset(mat);return mat
steel=material('M_Trial_Steel',(.15,.17,.20),.75)
body=material('M_Trial_Body',(.34,.44,.52),.25)
joint=material('M_Trial_Joints',(.018,.024,.030))
floor=material('M_Trial_Floor',(.045,.054,.062))
slots=list(mesh.materials)
for slot in slots:
    name=str(slot.material_slot_name)
    slot.material_interface=steel if 'Hammer' in name else joint if 'Joint' in name else body
mesh.materials=slots;ed.save_loaded_asset(mesh);ed.save_loaded_asset(anim)

levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
if ed.does_asset_exist(BASE+'/AnimationTrial'):
    world=levels.load_level(BASE+'/AnimationTrial')
    labels={'Trial floor','Key','Fill','Rim','Fixed exposure','Community source','Hammer timing trial','Label_0','Label_1','Comparison camera','Auto play animation comparison','Offstage player start'}
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label() in labels:actors.destroy_actor(actor)
else:world=levels.new_level(BASE+'/AnimationTrial')
assert world
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',u.GameModeBase)
def spawn(cls,name,pos,rot=u.Rotator(pitch=0,yaw=0,roll=0)):
    a=actors.spawn_actor_from_class(cls,u.Vector(*pos),rot);a.set_actor_label(name);return a
ground=spawn(u.StaticMeshActor,'Trial floor',(0,0,-7))
ground.static_mesh_component.set_static_mesh(ed.load_asset('/Engine/BasicShapes/Cube.Cube'))
ground.set_actor_scale3d(u.Vector(14,16,.12));ground.static_mesh_component.set_material(0,floor)
for name,pos,color in [('Key',(260,-260,400),(1,.85,.67)),('Fill',(100,360,300),(.55,.72,1)),('Rim',(-240,0,380),(1,.75,.4))]:
    a=spawn(u.PointLight,name,pos);a.point_light_component.set_intensity(18000)
    a.point_light_component.set_attenuation_radius(1700);a.point_light_component.set_light_color(u.LinearColor(*color,1))
pp=spawn(u.PostProcessVolume,'Fixed exposure',(0,0,0));pp.set_editor_property('unbound',True)
settings=pp.settings
settings.set_editor_property('override_auto_exposure_method',True);settings.auto_exposure_method=u.AutoExposureMethod.AEM_MANUAL
settings.set_editor_property('override_auto_exposure_bias',True);settings.auto_exposure_bias=-8
settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True);settings.auto_exposure_apply_physical_camera_exposure=False
pp.settings=settings

sequence=ed.load_asset(BASE+'/LS_AnimationComparison') or tools.create_asset('LS_AnimationComparison',BASE,u.LevelSequence,u.LevelSequenceFactoryNew())
for b in sequence.get_bindings():b.remove()
for t in sequence.get_tracks():sequence.remove_track(t)
sequence.set_display_rate(u.FrameRate(60,1));sequence.set_playback_start(0);sequence.set_playback_end(252)
specs=[]
for index,(y,rate) in enumerate([(145,1.),(-145,.62)]):
    a=spawn(u.SkeletalMeshActor,'Community source' if index==0 else 'Hammer timing trial',(0,y,0),u.Rotator(pitch=0,yaw=-90,roll=0))
    comp=a.skeletal_mesh_component;comp.set_skeletal_mesh_asset(mesh)
    comp.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    binding=sequence.add_possessable(a);track=binding.add_track(u.MovieSceneSkeletalAnimationTrack)
    section=track.add_section();section.set_range(0,252)
    params=section.params;params.animation=anim
    params.play_rate=u.MovieSceneTimeWarpExtensions.make_time_warp(rate);section.params=params
    specs.append({'actor':a.get_path_name(),'rate':rate})
    text=spawn(u.TextRenderActor,'Label_'+str(index),(50,y,210),u.Rotator(pitch=0,yaw=0,roll=0))
    text.text_render.set_text('SOURCE / 1.00x' if index==0 else 'HAMMER STUDY / 0.62x')
    text.text_render.set_world_size(16);text.text_render.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
    text.text_render.set_text_render_color(u.Color(r=120,g=190,b=235,a=255) if index==0 else u.Color(r=245,g=180,b=85,a=255))
spawn(u.PlayerStart,'Offstage player start',(2000,0,100))
camera=spawn(u.CameraActor,'Comparison camera',(680,0,295),u.Rotator(pitch=-16,yaw=180,roll=0))
camera.camera_component.set_field_of_view(54)
camera.set_editor_property('auto_activate_for_player',u.AutoReceiveInput.PLAYER0)
binding=sequence.add_possessable(camera)
cut=sequence.add_track(u.MovieSceneCameraCutTrack).add_section();cut.set_range(0,252)
bid=u.MovieSceneObjectBindingID();bid.set_editor_property('guid',binding.get_id());cut.set_camera_binding_id(bid)
player=spawn(u.LevelSequenceActor,'Auto play animation comparison',(0,0,0));player.set_sequence(sequence)
play=player.get_editor_property('playback_settings');play.auto_play=True;play.loop_count=u.MovieSceneSequenceLoopCount(-1)
player.set_editor_property('playback_settings',play)
ed.save_loaded_asset(sequence);levels.save_current_level()
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(680,0,295),u.Rotator(pitch=-16,yaw=180,roll=0))
u.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
u.LevelSequenceEditorBlueprintLibrary.set_current_time(30)
u.LevelSequenceEditorBlueprintLibrary.set_lock_camera_cut_to_viewport(True)
u.LevelSequenceEditorBlueprintLibrary.play()
report={'state':'completed','mesh':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'animation':anim.get_path_name(),
    'length_seconds':anim.sequence_length,'actors':specs,'map':BASE+'/AnimationTrial',
    'sequence':sequence.get_path_name(),'note':'Community sword slash plus simple hammer, source and 0.62x. Not a production heavy hammer attack.'}
(ROOT/'Saved/AnimationTrial/import-result.json').write_text(json.dumps(report,indent=2))
