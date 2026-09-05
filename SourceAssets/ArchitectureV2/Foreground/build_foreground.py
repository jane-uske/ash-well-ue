"""Additional entrance dressing; does not replace the existing mine frame.
Read-only dependency: ../build_architecture_v2.py supplies tested mesh/FBX helpers.
All coordinates are metres, shared zero origin, X forward/Y right/Z up.
"""
from pathlib import Path
helper_path=Path(__file__).resolve().parent.parent/'build_architecture_v2.py'
# Execute only helper definitions and material setup, not the architecture generator.
helper_source=helper_path.read_text().split('\nchunks=[]\n')[0]
exec(compile(helper_source,str(helper_path),'exec'),globals())
random.seed(98214)
steel=Mesh('SM_AV2_FG_LayeredSteel',.008)
pipes=Mesh('SM_AV2_FG_PipeJoints',.005)
cables=Mesh('SM_AV2_FG_CablesAndDrips',0)

def elliptical_rib(x,ycenter=.45,width=5.70,base=3.05,rise=1.63):
    for side in [-1,1]:
        y=ycenter+side*width/2
        # A layered section: thin flanges and recessed web, never a solid tunnel wall.
        for dx,w,d in [(-.17,.075,.30),(.17,.075,.30),(0,.27,.085)]:steel.box((x+dx,y,1.55),(w,d,3.10),'Rust')
        steel.box((x,y,.12),(.60,.55,.20),'DarkSteel')
        for z in [.55,1.65,2.75]:
            steel.box((x-.23,y,z),(.075,.53,.43),'DarkSteel')
            steel.box((x-.28,y+.035,z+.035),(.050,.40,.32),'Rust')
            for dy in [-.16,.16]:
                for dz in [-.125,.125]:steel.tube((x-.32,y+dy,z+dz),(x-.375,y+dy,z+dz),.030,'DarkSteel',6)
    for i in range(44):
        a=i*math.pi/44;b=(i+1)*math.pi/44
        # Three extruded bands follow the oval opening, separated by shadow gaps.
        for dx,offset,rad in [(-.18,0,.072),(.18,0,.072),(0,.08,.066)]:
            p=(x+dx,ycenter+(width/2+offset)*math.cos(a),base+(rise+offset)*math.sin(a))
            q=(x+dx,ycenter+(width/2+offset)*math.cos(b),base+(rise+offset)*math.sin(b))
            steel.beam(p,q,rad*2,.19 if dx else .26,'Rust')
        if i%4==0:
            t=(a+b)/2;yy=ycenter+width/2*math.cos(t);zz=base+rise*math.sin(t)
            steel.box((x-.255,yy,zz),(.060,.23,.21),'DarkSteel')
            steel.tube((x-.29,yy,zz),(x-.35,yy,zz),.029,'Rust',6)

elliptical_rib(4.9,ycenter=1.20,width=7.20)
elliptical_rib(7.65,ycenter=2.025,width=8.95,base=3.10,rise=1.73)
# Short diagonal braces, lapped plates, small brackets at left edge.
for x in [4.9,7.65]:
    steel.beam((x,-2.36,2.65),(x,-1.65,3.63),.12,.19,'DarkSteel')
    for z in [.8,2.1,3.0]:
        steel.box((x-.25,-2.34,z),(.1,.72,.26),'Rust')
        for y in [-2.61,-2.10]:steel.tube((x-.31,y,z),(x-.37,y,z),.035,'DarkSteel',6)
for y,z in [(-2.33,3.08),(-1.95,3.65),(5.25,3.2)]:
    steel.beam((3.8,y,z),(8.15,y,z),.085,.15,'DarkSteel')

# Rusty pipes stay on the flanks/ceiling; short offsets make joints dimensional.
for x0,x1,y,z,r in [(2.7,8.2,-2.26,3.32,.105),(3.0,8.5,-2.09,3.55,.049),(3.8,8.3,5.25,3.62,.065)]:
    pipes.tube((x0,y,z),(x1,y,z),r,'Rust',16)
    for x in [4.0,5.8,7.5]:
        pipes.flange((x,y,z),(1,0,0),r)
        pipes.box((x,y,z+.18),(.12,.23,.22),'DarkSteel')
        pipes.beam((x,y,z+.12),(x,y-.30 if y<0 else y+.30,z+.22),.075,.055,'DarkSteel')
    if y<0:
        pts=[(x1+.22*math.sin(t*math.pi/2),y,z-.22*(1-math.cos(t*math.pi/2))) for t in [i/16 for i in range(17)]]
        pipes.line(pts,r,'Rust',12)
        pipes.tube(pts[-1],(x1+.22,y,z-.80),r,'Rust',12)
# A valve handle is visible on the upper left pipe.
pipes.ring((5.95,-2.11,3.35),.16,.020,'DarkSteel',24,8,'X')
for i in range(5):
    t=i*math.tau/5;pipes.beam((5.95,-2.11,3.35),(5.95,-2.11+.15*math.cos(t),3.35+.15*math.sin(t)),.015,.02,'DarkSteel')

# Hanging cables form irregular catenary-like strands along the upper frame.
for i in range(8):
    x=4.2+i*.43;left=-2.34;right=5.1;z=4.21+(i%3)*.10;sag=.50+random.random()*.38
    pts=[]
    for j in range(47):
        t=j/46;pts.append((x+.13*math.sin(t*math.pi),left+(right-left)*t,z-4*sag*t*(1-t)))
    cables.line(pts,.010+(i%3)*.0035,'DarkSteel',6)
for i in range(11):
    x=random.uniform(4.5,8.0);y=random.choice([-1,1])*random.uniform(1.55,2.55);z=random.uniform(3.45,4.30);drop=random.uniform(.20,.75)
    cables.line([(x,y,z),(x+.04,y+.025,z-drop*.4),(x+.03,y+.03,z-drop)],.0065,'DarkSteel',5)
# Thin tapered mineral formations cling to the top-left opening; no large stalactites.
for i in range(35):
    x=random.uniform(4.4,8.15);y=random.uniform(-2.40,-.55);z=3.27+1.05*math.sqrt(max(0,1-((y-.45)/2.85)**2));length=random.uniform(.09,.42)
    r=random.uniform(.008,.022)
    cables.tube((x,y,z),(x+.015,y+.01,z-length*.72),r,'Rock',7,r*.38)
    cables.tube((x+.015,y+.01,z-length*.72),(x+.015,y+.01,z-length),r*.38,'Rock',7,.0013)

manifest={'version':2,'source_units':'metres','axes':{'forward':'+X','right':'+Y','up':'+Z'},'shared_origin':[0,0,0],'ue_actor_scale':[1,-1,1],'fbx_axis_forward':'-Y','fbx_axis_up':'Z','material_slots':NAMES,'uv_repeat_metres':1.5,'purpose':'Additional thin entrance framing. Left jambs stay at -2.40/-2.45m; right jambs widened to 4.8/6.5m to reveal the near pier.','helper_dependency':'../build_architecture_v2.py','chunks':[]}
for mesh in [steel,pipes,cables]:manifest['chunks'].append(mesh.finish())
manifest['triangles']=sum(c['triangles'] for c in manifest['chunks'])
assert manifest['triangles']<=200000,manifest['triangles']
(ROOT/'foreground_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Foreground_Source.blend'))
print('DONE',manifest['triangles'],flush=True)
