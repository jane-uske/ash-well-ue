import unreal as u
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert '/Terrace/' in u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name()
assert not levels.is_in_play_in_editor()
levels.editor_request_begin_play()
