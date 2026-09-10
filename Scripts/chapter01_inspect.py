import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];ed=u.EditorAssetLibrary;levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
target='/Game/AshWell/Chapter01/L_Chapter01_Descent'
if not ed.does_asset_exist(target):target='/Game/AshWell/Maps/FirstDescentIntro'
assert not levels.is_in_play_in_editor();levels.load_level(target)
rows=[]
for a in actors.get_all_level_actors():
 c=a.get_component_by_class(u.StaticMeshComponent);mesh=c.static_mesh if c else None
 rows.append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'location':str(a.get_actor_location()),'mesh':mesh.get_path_name() if mesh else None})
report={'map':target,'actors':len(rows),'details':rows};(R/'Saved/Chapter01/inspect.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));report={'map':target,'actors':len(rows),'report':'Saved/Chapter01/inspect.json'}
