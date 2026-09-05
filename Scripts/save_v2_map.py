import unreal as u
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/AshWell/Maps/FirstDescentV02Final')
u.log('ASHWELL: Saved the revised scene to FirstDescentV02')
