from pathlib import Path
import unreal as u,json
from editor_toolset.toolsets.blueprint import BlueprintTools as B
out=Path(__file__).resolve().parents[1]/'Saved/Terrace'
bp=u.EditorAssetLibrary.load_asset('/Game/AshWell/Terrace/BP_TerraceProbe')
g=B.get_graph(bp,'EventGraph')
selected=['AddEvent|EventTick','AddEvent|EventBeginPlay','Game|GetPlayerCharacter','Game|GetPlayerController','Transformation|GetActorLocation','Transformation|SetActorLocation','Transformation|GetDistanceTo','Game|Player|IsInputKeyDown','Collision|SetActorEnableCollision','Development|PrintString','Math|Vector|MakeVector']
report={}
for name in selected:
 info=B.get_node_type_pins(g,name)
 report[name]={'inputs':[{'name':str(p.name),'type':str(p.type_id),'value':str(p.value)} for p in info.input_pins],'outputs':[{'name':str(p.name),'type':str(p.type_id)} for p in info.output_pins]}
report['valid']=list(B.find_node_types(g,'IsValid'))
report['play_methods']=[n for n in dir(u.LevelEditorSubsystem) if 'play' in n]
report['take_shot']=u.AutomationLibrary.take_high_res_screenshot.__doc__
(out/'node-pins.json').write_text(json.dumps(report,indent=2))
