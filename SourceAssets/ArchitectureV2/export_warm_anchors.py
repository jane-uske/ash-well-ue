"""Extract small warm-light positions from the actual exported room-window mesh.
Run with Blender --background ServiceRefinement_Source.blend --python this file.
"""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
obj=bpy.data.objects['SM_AV2_Windows_And_Lamps'];mesh=obj.data
adj=[[] for v in mesh.vertices]
for e in mesh.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();centers=[]
for first in range(len(mesh.vertices)):
    if first in seen:continue
    todo=[first];seen.add(first);component=[]
    while todo:
        v=todo.pop();component.append(v)
        for n in adj[v]:
            if n not in seen:seen.add(n);todo.append(n)
    center=[sum(mesh.vertices[i].co[k] for i in component)/len(component) for k in range(3)]
    x,y,z=center
    if 90<=x<=100 and -20<=y<=25 and -25<=z<=12:centers.append(center)
groups=[]
for center in sorted(centers,key=lambda p:(p[2],p[1])):
    group=next((g for g in groups if abs(g[0][0]-center[0])<.1 and abs(g[0][2]-center[2])<.1 and abs(g[0][1]-center[1])<.70),None)
    if group:group.append(center)
    else:groups.append([center])
positions=[[sum(p[k] for p in group)/len(group) for k in range(3)] for group in groups]
if len(positions)>12:positions=[positions[round(i*(len(positions)-1)/11)] for i in range(12)]
anchors=[]
for i,p in enumerate(positions):
    anchors.append({'name':'WarmRoom_'+str(i+1).zfill(2),'position_m':[round(p[0]-.35,4),round(p[1],4),round(p[2],4)],'window_center_m':[round(q,4) for q in p],'temperature_kelvin':2350,'suggested_lumens':[260,340,420][i%3],'suggested_radius_m':3.6,'notes':'Inside the actual open window reveal, in front of the dark recessed back panel.'})
report={'source_units':'metres','axes':{'forward':'+X','right':'+Y','up':'+Z'},'ue_position':'Multiply these source coordinates by 100. They are already in the intended world convention; geometry actors use mirror-Y only to compensate their FBX import.','derived_from':'ServiceRefinement_Source.blend / SM_AV2_Windows_And_Lamps connected components','anchor_count':len(anchors),'anchors':anchors}
(ROOT/'warm_room_light_anchors.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False),flush=True)
