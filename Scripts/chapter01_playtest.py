"""Read-only collision probe at a failed route position, through native UE MCP."""
import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'Saved/Chapter01/runtime.json').read_text());w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
p=u.Vector(d['x'],d['y'],d['z']);report={'position':[p.x,p.y,p.z],'traces':[]}
for delta in [u.Vector(80,0,0),u.Vector(80,0,-18),u.Vector(80,0,30)]:
 h=u.SystemLibrary.capsule_trace_single(w,p,p+delta,28,86,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
 report['traces'].append(str(h))
(R/'Saved/Chapter01/collision-probe.json').write_text(json.dumps(report,indent=2))
