import unreal as u,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'Saved/Terrace'
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert '/Terrace/' in world.get_path_name()
report={'world':world.get_path_name(),'request_play':u.LevelEditorSubsystem.editor_request_begin_play.__doc__,'game_world':u.UnrealEditorSubsystem.get_game_world.__doc__,'pc_methods':[x for x in dir(u.PlayerController) if any(t in x for t in ['input_key','control_rotation','press','input_axis'])],'actor_methods':[x for x in dir(u.Actor) if any(t in x for t in ['call_method','actor_location'])],'world_settings':str(world.get_world_settings().get_editor_property('default_game_mode'))}
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
report['gate']=[{'path':a.get_path_name(),'tick':a.is_actor_tick_enabled(),'start_tick':a.get_editor_property('primary_actor_tick').get_editor_property('start_with_tick_enabled'),'open':a.get_editor_property('GateOpen')} for a in actors if 'ReturnGate' in a.get_actor_label()]
(out/'inspect.json').write_text(json.dumps(report,indent=2))
u.EditorLevelLibrary.editor_set_game_view(True)
u.AutomationLibrary.take_high_res_screenshot(1440,900,str(root/'Docs/Verification/Terrace/editor-overlook.png'))
