from pathlib import Path
import unreal as u,json
from editor_toolset.toolsets.blueprint import BlueprintTools as B
BASE='/Game/AshWell/Terrace';ed=u.EditorAssetLibrary;OUT=Path(__file__).resolve().parents[1]/'Saved/Terrace'
bp=ed.load_asset(BASE+'/BP_TerraceGate') or B.create(BASE,'BP_TerraceGate',u.StaticMeshActor.static_class())
if 'GateOpen' not in [str(v) for v in B.list_variables(bp)]: B.add_variable(bp,'GateOpen','bool')
B.compile_blueprint(bp);g=B.get_graph(bp,'EventGraph')
report={}
for term in ['GetGateOpen','SetGateOpen','IsValid','MakeKey']:
 report[term]=list(B.find_node_types(g,term))
for name in ['Utilities|IsValid','Variables|Default|GetGateOpen','Variables|Default|SetGateOpen']:
 info=B.get_node_type_pins(g,name)
 report[name]={'in':[(str(p.name),str(p.type_id),str(p.value)) for p in info.input_pins],'out':[(str(p.name),str(p.type_id)) for p in info.output_pins]}
ed.save_loaded_asset(bp)
(OUT/'gate-node-pins.json').write_text(json.dumps(report,indent=2))
