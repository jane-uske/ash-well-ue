import unreal as u
if hasattr(u,'_terrace_route_handle'):
 try:u.unregister_slate_post_tick_callback(u._terrace_route_handle)
 except Exception:pass
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play()
