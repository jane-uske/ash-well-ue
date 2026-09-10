"""Request an orderly editor exit on a later UI tick, after returning the MCP reply."""
import unreal as u,time
shutdown_at=time.monotonic()+1.0
shutdown_handle=None
def shutdown_tick(delta):
 global shutdown_handle
 if time.monotonic()>=shutdown_at:
  u.unregister_slate_post_tick_callback(shutdown_handle)
  u.SystemLibrary.quit_editor()
shutdown_handle=u.register_slate_post_tick_callback(shutdown_tick)
report={'shutdown_scheduled':True}
