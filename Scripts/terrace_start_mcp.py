"""Start the built-in MCP server for this editor process only."""
import unreal as u
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert '/Terrace/' in w.get_path_name()
u.SystemLibrary.execute_console_command(w,'ModelContextProtocol.StartServer 19852')
