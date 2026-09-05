import gc
import unreal as u
gc.collect()
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/AshWell/Maps/FirstDescentV02Final')
camera=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='AW_HeroCamera')
u.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(),camera.get_actor_rotation())
u.EditorLevelLibrary.editor_set_game_view(True)
