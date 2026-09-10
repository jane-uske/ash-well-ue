import unreal as u,json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as B
OUT=Path(__file__).resolve().parents[1]/'Saved/Terrace';BASE='/Game/AshWell/Terrace'
ed=u.EditorAssetLibrary
bp=ed.load_asset(BASE+'/BP_TerraceProbe') or B.create(BASE,'BP_TerraceProbe',u.StaticMeshActor.static_class())
g=B.get_graph(bp,'EventGraph')
queries=['EventBeginPlay','EventTick','GetPlayerCharacter','GetActorLocation','SetActorLocation','GetPlayerController','IsInputKeyDown','E','SetActorHiddenInGame','SetActorEnableCollision','GetDistanceTo','PrintString','Vector_Distance','SetWorldLocation','SetActorRelativeLocation','SetActorRotation']
report={}
for term in queries:
 found=B.find_node_types(g,term)
 report[term]=found[:35]
(OUT/'node-types.json').write_text(json.dumps(report,indent=2,default=str))
(OUT/'dsl-docs.txt').write_text(B.get_graph_dsl_docs())
(OUT/'api.txt').write_text(str(u.BlueprintEditorLibrary.add_member_variable.__doc__))
