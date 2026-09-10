from pathlib import Path
import unreal as u,json
from editor_toolset.toolsets.blueprint import BlueprintTools as B
root=Path(__file__).resolve().parents[1];out=root/'Saved/Terrace'
bp=u.load_object(None,'/Game/AshWell/Terrace/BP_TerraceGate.BP_TerraceGate');g=B.get_graph(bp,'EventGraph')
(out/'gate-dsl.txt').write_text(B.read_graph_dsl(g))
report={}
for term in ['WasInputKeyJustPressed','InputKey','EnableInput']:
 report[term]=list(B.find_node_types(g,term))
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world();pc=u.GameplayStatics.get_player_controller(w,0)
report['paused']=u.GameplayStatics.is_game_paused(w)
report['controller']=pc.get_path_name()
report['tick']=[a.is_actor_tick_enabled() for a in u.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())]
(out/'gate-probe.json').write_text(json.dumps(report,indent=2))
