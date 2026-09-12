import unreal as u,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];B='/Game/AshWell/MountedBoss/ReferenceProduction';mesh=u.EditorAssetLibrary.load_asset(B+'/SM_ReferenceField')
queries=[u.Vector(x,y,0) for x,y in [(0,0),(600,0),(-600,0),(0,600),(0,-600),(2000,1000),(-2000,-1000)]]
points=u.AshWellReferenceEnvironmentTools.inspect_fallback_vertices(mesh,queries)
settings=u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_nanite_settings(mesh)
r={'closest_fallback_vertices':[[p.x,p.y,p.z] for p in points],'settings':str(settings),'bounds':str(mesh.get_bounds())}
(R/'Saved/MountedReferenceProduction/surface-audit.json').write_text(json.dumps(r,indent=2));u.log('SURFACE_AUDIT '+json.dumps(r))
if __import__('os').environ.get('ASHWELL_REFERENCE_CHAINED')!='1':
    u.EditorPythonScripting.set_keep_python_script_alive(True);finish=time.monotonic()
    def quit_ready(dt):
     if time.monotonic()-finish>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    handle=u.register_slate_post_tick_callback(quit_ready)
