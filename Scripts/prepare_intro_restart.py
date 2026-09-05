import unreal as u
ed=u.EditorAssetLibrary
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
level.save_current_level();ed.save_directory('/Game/AshWell',only_if_is_dirty=True,recursive=True)
path='/Game/AshWell/Maps/FirstDescentIntro'
if not ed.does_asset_exist(path):
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert u.EditorLoadingAndSavingUtils.save_map(world,path)
u.SystemLibrary.quit_editor()
