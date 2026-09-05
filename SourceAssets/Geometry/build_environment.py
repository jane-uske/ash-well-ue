"""Ash Well first descent environment, original procedural geometry.

Run with Blender 5.2 --background --python build_environment.py.
Authored coordinates are metres: X forward, Y right, Z up. Each FBX has origin 0.
No downloaded or licensed third-party geometry is used.
"""
import bpy, bmesh, math, random, json, sys
from pathlib import Path
from mathutils import Vector
from mathutils import noise

ROOT = Path(__file__).resolve().parent
ROCKS_ONLY = '--rocks-only' in sys.argv
ROCK_CHUNKS = {'SM_MineRock_Left','SM_MineRock_Right','SM_MineRoof','SM_FarCavern_Left','SM_FarCavern_Center','SM_FarCavern_Right','SM_CavernCeiling','SM_SideCliffLower'}
random.seed(1905)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0
MATERIAL_NAMES = ['Rock', 'Rust', 'Concrete', 'DarkSteel', 'Amber', 'Cloth']
COLORS = [(0.105,0.119,0.12,1),(0.18,0.08,0.035,1),(0.20,0.205,0.19,1),(0.045,0.052,0.06,1),(1,0.40,0.08,1),(0.055,0.062,0.058,1)]
MATERIALS=[]
for name,col in zip(MATERIAL_NAMES,COLORS):
    m=bpy.data.materials.new(name); m.diffuse_color=col; m.use_nodes=True
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if p is None:
        p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(p.outputs['BSDF'],output.inputs['Surface'])
    p.inputs['Base Color'].default_value=col
    p.inputs['Roughness'].default_value=0.78
    if name in ['Rust','DarkSteel']: p.inputs['Metallic'].default_value=0.65
    if name=='Amber':
        p.inputs['Emission Color'].default_value=col; p.inputs['Emission Strength'].default_value=2
    MATERIALS.append(m)

class Build:
    def __init__(self,name,bevel=0): self.name=name; self.v=[]; self.f=[]; self.mi=[]; self.bevel=bevel
    def add(self,verts,faces,mat):
        n=len(self.v); self.v.extend(verts); self.f.extend([tuple(n+i for i in f) for f in faces]); self.mi.extend([MATERIAL_NAMES.index(mat)]*len(faces))
    def box(self,c,s,mat='DarkSteel',yaw=0):
        c=Vector(c); co=math.cos(yaw); si=math.sin(yaw)
        vs=[]
        for z in [-1,1]:
            for y in [-1,1]:
                for x in [-1,1]:
                    dx=x*s[0]/2; dy=y*s[1]/2
                    vs.append(tuple(c+Vector((dx*co-dy*si,dx*si+dy*co,z*s[2]/2))))
        self.add(vs,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat)
    def tube(self,a,b,r,mat='DarkSteel',n=12,r2=None):
        a=Vector(a); b=Vector(b); axis=(b-a).normalized(); u=axis.cross(Vector((0,0,1)))
        if u.length<0.01: u=axis.cross(Vector((0,1,0)))
        u.normalize(); v=axis.cross(u).normalized(); vs=[]
        for center,rad in [(a,r),(b,r if r2 is None else r2)]:
            for i in range(n):
                ang=i*math.tau/n; vs.append(tuple(center+rad*(math.cos(ang)*u+math.sin(ang)*v)))
        faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]
        faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(vs,faces,mat)
    def line(self,points,r,mat='DarkSteel',n=8):
        for a,b in zip(points,points[1:]): self.tube(a,b,r,mat,n)
    def rock(self,c,s,seed,detail=2):
        rng=random.Random(seed); bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=detail,radius=1)
        bm.verts.ensure_lookup_table(); bm.verts.index_update(); verts=[]
        for vert in bm.verts:
            p=vert.co; perturb=1+rng.uniform(-0.23,0.23)+0.10*math.sin(p.x*8+p.z*3)
            verts.append((c[0]+p.x*s[0]*perturb,c[1]+p.y*s[1]*perturb,c[2]+p.z*s[2]*perturb))
        faces=[tuple(v.index for v in f.verts) for f in bm.faces]; bm.free()
        if detail>=3:
            # Keep the previous per-rock bounds, but replace independent vertex jitter
            # with densely sampled, spatially coherent eroded rock morphology.
            old_min=[min(p[k] for p in verts) for k in range(3)]
            old_max=[max(p[k] for p in verts) for k in range(3)]
            fine=bmesh.new(); bmesh.ops.create_icosphere(fine,subdivisions=5,radius=1)
            fine.verts.ensure_lookup_table(); fine.verts.index_update()
            nr=random.Random(seed+8417); offset=Vector(tuple(nr.uniform(-40,40) for _ in range(3)))
            fractures=[]
            for i in range(3):
                normal=Vector((nr.uniform(-1,1),nr.uniform(-1,1),nr.uniform(-.45,.45))).normalized()
                fractures.append((normal,nr.uniform(-.45,.45),nr.uniform(.025,.055),nr.uniform(.03,.075)))
            refined=[]
            for vert in fine.verts:
                u=vert.co.copy()
                # Slightly blocky strata without exposed triangular crystal faces.
                p=Vector(tuple(math.copysign(abs(q)**.84,q) for q in u))
                q=p+offset
                shape=1+.105*noise.noise(q*2.0)+.040*noise.noise(q*5.8)+.017*noise.noise(q*16.0)
                # Narrow erosion along a few irregular geological fracture planes.
                for normal,cut,width,depth in fractures:
                    d=abs(p.dot(normal)-cut+.023*noise.noise(q*8))
                    shape-=depth*math.exp(-((d/width)**2))
                bedding=p.z*11+.42*noise.noise(q*3)
                shape+=.011*math.sin(bedding)+.007*noise.noise(q*33)
                refined.append(tuple(p*shape))
            new_min=[min(p[k] for p in refined) for k in range(3)]
            new_max=[max(p[k] for p in refined) for k in range(3)]
            verts=[tuple(old_min[k]+(p[k]-new_min[k])/(new_max[k]-new_min[k])*(old_max[k]-old_min[k]) for k in range(3)) for p in refined]
            faces=[tuple(v.index for v in f.verts) for f in fine.faces]; fine.free()
        self.add(verts,faces,'Rock')
    def arch(self,x,y,z,width,height,thick,depth,mat='Concrete',segments=24):
        # Spring points at y +/- width/2, apex z+height. Arch in YZ plane.
        for i in range(segments):
            a=i*math.pi/segments; b=(i+1)*math.pi/segments
            def p(t,outer):
                return (y+(width/2+outer*thick)*math.cos(t),z+(height+outer*thick)*math.sin(t))
            vs=[]
            for xx in [x-depth/2,x+depth/2]:
                for t,o in [(a,0),(b,0),(b,1),(a,1)]:
                    yy,zz=p(t,o); vs.append((xx,yy,zz))
            self.add(vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def finish(self):
        mesh=bpy.data.meshes.new(self.name); mesh.from_pydata(self.v,[],self.f); mesh.update()
        obj=bpy.data.objects.new(self.name,mesh); bpy.context.collection.objects.link(obj)
        for mat in MATERIALS: mesh.materials.append(mat)
        for poly,mi in zip(mesh.polygons,self.mi): poly.material_index=mi
        bpy.context.view_layer.objects.active=obj; obj.select_set(True)
        if self.bevel:
            mod=obj.modifiers.new('Small manufactured edge bevels','BEVEL'); mod.width=self.bevel; mod.segments=2; mod.limit_method='ANGLE'; mod.angle_limit=0.52
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.dissolve_degenerate(bm,dist=0.000001,edges=list(bm.edges))
        tiny=[f for f in bm.faces if f.calc_area()<1e-10]
        if tiny:bmesh.ops.delete(bm,geom=tiny,context='FACES_ONLY')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        if self.name in ROCK_CHUNKS:
            for face in bm.faces: face.smooth=True
            # Smooth weathered surfaces while retaining unusually sharp fissures.
            for edge in bm.edges:
                if len(edge.link_faces)==2: edge.smooth=edge.calc_face_angle(0)<math.radians(48)
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
        # Planar projection by each face's dominant axis, 1 UV repeat per 1.5 metres.
        # World-anchored UV scale is consistent across modular chunks.
        mesh=obj.data; uv=mesh.uv_layers.new(name='UVMap')
        for poly in mesh.polygons:
            normal=poly.normal; axis=max(range(3),key=lambda k:abs(normal[k]))
            axes=[k for k in range(3) if k!=axis]
            for li in poly.loop_indices:
                p=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(p[axes[0]]/1.5,p[axes[1]]/1.5)
        mesh.calc_loop_triangles()
        coords=[v.co for v in mesh.vertices]
        bounds={'min':[round(min(v[k] for v in coords),4) for k in range(3)],'max':[round(max(v[k] for v in coords),4) for k in range(3)]}
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        # Blender native -Y forward / Z up metadata. Geometry coordinates remain X/Y/Z.
        bpy.ops.export_scene.fbx(filepath=str(ROOT/(self.name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,mesh_smooth_type='EDGE' if self.name in ROCK_CHUNKS else 'FACE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
        result={'name':self.name,'file':self.name+'.fbx','vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'bounds_m':bounds,'origin_m':[0,0,0],'material_slots':MATERIAL_NAMES}
        obj.select_set(False); print('EXPORTED',json.dumps(result),flush=True); return result

chunks=[]
def chunk(name,bevel=0):
    b=Build(name,bevel); chunks.append(b); return b

# Portal: organic surface relief replaces the spherical low-detail greybox cave.
for side,label in [(-1,'Left'),(1,'Right')]:
    b=chunk('SM_MineRock_'+label)
    for ix,x in enumerate([-6,-3.4,-0.8,1.8,4.0]):
        for iz,z in enumerate([0.2,2.2,4.4,6.3]):
            y=side*(3.5+random.uniform(-0.25,0.35))
            b.rock((x,y,z),(2.0,1.0+random.random()*.35,1.7),1000+ix*40+iz+int(side*20),3)
    for i in range(24):
        b.rock((random.uniform(-5,4),side*random.uniform(2.6,3.1),random.uniform(-.2,.12)),(.12+random.random()*.3,.18+random.random()*.25,.06+random.random()*.12),2100+i+int(side*100),1)
b=chunk('SM_MineRoof')
for i,x in enumerate([-6,-3,0,3]):
    for j,y in enumerate([-2,0,2]): b.rock((x,y,6.15),(2.1,1.75,.9),3100+i*8+j,3)
b=chunk('SM_MineSteelFrames',.026)
for x in [-4.5,-.4,3.0]:
    for y in [-2.72,2.72]:
        b.box((x,y,2.0),(.24,.25,4.0),'Rust'); b.box((x,y,.18),(.58,.65,.28),'Rust')
        for z in [.6,1.9,3.2]:
            b.box((x-.14,y,z),(.055,.53,.45),'Rust')
            for dy in [-.17,.17]:
                b.tube((x-.19,y+dy,z-.13),(x-.24,y+dy,z-.13),.044,'DarkSteel',8)
                b.tube((x-.19,y+dy,z+.13),(x-.24,y+dy,z+.13),.044,'DarkSteel',8)
    b.arch(x,0,3.6,5.45,1.7,.25,.25,'Rust',24)

def route(t):
    if t<=12:return Vector((-6+t,0,0))
    q=(t-12)/20; return Vector((6+18*q,8*q*q*(3-2*q),0))
def frame(t):
    p=route(t); tan=(route(min(32,t+.03))-route(max(0,t-.03))).normalized(); side=Vector((-tan.y,tan.x,0)); return p,tan,side

b=chunk('SM_WalkwayDeck',.015)
for i in range(44):
    ta=i*32/44; tb=(i+1)*32/44; p,tan,side=frame((ta+tb)/2); length=(route(tb)-route(ta)).length-.025; yaw=math.atan2(tan.y,tan.x)
    if i%6==2 or i%6==3:
        b.box(tuple(p+Vector((0,0,-.055))),(length,2.98,.11),'Rust',yaw)
        for sy in [-1.05,0,1.05]:
            for sx in [-length*.36,length*.36]:
                q=p+tan*sx+side*sy; b.tube(tuple(q+Vector((0,0,0))),tuple(q+Vector((0,0,.014))),.027,'DarkSteel',6)
    else:
        for lane in [-1,0,1]:
            q=p+side*(lane*.994); b.box(tuple(q+Vector((0,0,-.095))),(length,.974,.18),'Concrete',yaw)
        if i%3==0:
            for j in range(4):
                q=p+side*random.uniform(-1.35,1.35)+tan*random.uniform(-.2,.2)
                b.rock(tuple(q+Vector((0,0,.015))),(random.uniform(.04,.14),random.uniform(.04,.13),.023),4200+i*10+j,1)
b=chunk('SM_WalkwayEdgeBeams',.023)
for i in range(32):
    p,tan,side=frame(i+.5); length=(route(i+1)-route(i)).length+.035; yaw=math.atan2(tan.y,tan.x)
    for sg in [-1,1]:
        c=p+side*(sg*1.52)
        b.box(tuple(c+Vector((0,0,-.22))),(length,.12,.46),'Rust',yaw)
        b.box(tuple(c+Vector((0,0,-.43))),(length,.28,.06),'Rust',yaw)
        b.box(tuple(c+Vector((0,0,-.025))),(length,.2,.05),'Rust',yaw)
b=chunk('SM_WalkwayRails',.013)
for sg in [-1,1]:
    pts=[]
    for i in range(65):
        p,tan,side=frame(i*.5); pts.append(p+side*(sg*1.47))
    for height,rad in [(1.05,.042),(.51,.021)]: b.line([tuple(p+Vector((0,0,height))) for p in pts],rad,'Rust',10)
    for i in range(23):
        p,tan,side=frame(i*32/22); q=p+side*(sg*1.47)
        b.tube(tuple(q+Vector((0,0,-.04))),tuple(q+Vector((0,0,1.08))),.038,'Rust',10)
        b.box(tuple(q+Vector((0,0,.015))),(.18,.18,.055),'DarkSteel')
        if i%2==0: b.tube(tuple(q+Vector((0,0,.25))),tuple(q-tan*.22+Vector((0,0,-.28))),.023,'DarkSteel',8)
b=chunk('SM_WalkwayUnderTruss',.02)
for i in range(4,32,3):
    p,tan,side=frame(i); left=p-side*1.52; right=p+side*1.52
    b.tube(tuple(left+Vector((0,0,-.40))),tuple(right+Vector((0,0,-.40))),.09,'DarkSteel',8)
    for sg in [-1,1]:
        q=p+side*(sg*1.52); nxt=route(min(32,i+3))+side*(sg*1.52)
        b.tube(tuple(q+Vector((0,0,-.42))),tuple(q+Vector((0,0,-2.2))),.075,'Rust',8)
        b.tube(tuple(q+Vector((0,0,-2.2))),tuple(nxt+Vector((0,0,-.42))),.065,'Rust',8)
        b.tube(tuple(q+Vector((0,0,-2.2))),tuple(nxt+Vector((0,0,-2.2))),.07,'DarkSteel',8)

b=chunk('SM_MinePipesAndCables',.011)
for k,(y,z,r) in enumerate([(-2.65,3.55,.17),(-2.54,4.10,.08),(2.72,2.80,.10)]):
    b.tube((-6,y,z),(4.8,y,z),r,'Rust',16)
    for x in [-4,-1,2,4.5]:
        b.tube((x-.04,y,z),(x+.04,y,z),r*1.35,'DarkSteel',16)
        b.box((x,y,z+.28),(.09,.13,.5),'DarkSteel')
for k in range(7):
    x=-3+k*.8; pts=[]
    for j in range(30):
        t=j/29; pts.append((x+.45*math.sin(t*math.pi),-2.8+5.6*t,5.1-(.5+(k%3)*.20)*math.sin(t*math.pi)))
    b.line(pts,.012+(k%2)*.006,'DarkSteel',6)
# A hanging cable stays to the right of the walkable space.
b.line([(2.8,2.6,5),(3.0,2.6,3.6),(3.1,2.6,1.4),(3.5,2.7,-.5),(4.2,2.8,-3)],.025,'DarkSteel',8)

# Monumental near pier: irregular tiering, vertical channels and small ledges.
b=chunk('SM_ColossalPierCore',.12)
cx,cy=50,22
for z,h,r in [(-61,22,7.0),(-37,25,6.5),(-10,28,6.1),(18,27,5.75),(44,24,5.4),(70,30,5.1),(99,30,4.9)]:
    b.tube((cx,cy,z-h/2),(cx,cy,z+h/2),r,'Concrete',20,r*.97)
for z in [-72,-50,-25,4,31,57,84,110]:
    b.tube((cx,cy,z-.42),(cx,cy,z+.42),7 if z<0 else 6.3,'Rust',20)
b=chunk('SM_ColossalPierRibs',.065)
for i in range(12):
    a=i*math.tau/12; r=6.1; x=cx+math.cos(a)*r; y=cy+math.sin(a)*r
    b.box((x,y,11),(.44,.60,155),'DarkSteel',a)
    for z in [-58,-39,-15,8,28,53,80]:
        b.box((x,y,z),(.70,.90,.60),'Rust',a)
        if i in [5,6,7,8] and z in [-39,8,53]:
            b.box((x-.12,y,z+1.4),(.15,.70,1.7),'DarkSteel',a)

b=chunk('SM_CivicHallMass',.16)
# Wings and recessed rear wall; front has open arcades rather than a sealed slab.
b.box((105,-14,8),(23,16,160),'Concrete')
b.box((110,52,11),(28,21,165),'Concrete')
b.box((119,20,18),(7,57,155),'Concrete')
for y in [-23,-6,12,31,44,64]:
    b.box((94,y,12),(6,3.2,175),'Concrete')
    b.box((90.8,y,12),(.65,1.4,166),'DarkSteel')
    for z in [-61,-28,8,43,78]: b.box((91.5,y,z),(7.2,5.7,1.45),'Rust')
for z in [-66,-32,2,36,70,100]:
    b.box((106,20,z),(25,89,1.4),'Concrete')
    b.box((92.9,20,z+1),(1.0,89,.40),'DarkSteel')
b=chunk('SM_CivicHallArcades',.065)
for y,w in [(-14,14),(3,16),(22,16),(37.5,10),(54,17)]:
    for z in [-25,10,45,78]:
        b.arch(91.8,y,z,w,12 if z<78 else 8,1.15,2.0,'Concrete',24)
        b.arch(90.65,y,z,w+.4,12.2 if z<78 else 8.2,.22,.35,'DarkSteel',24)
        for sg in [-1,1]: b.box((91.5,y+sg*w/2,z-8),(1.8,1.2,16),'Concrete')
b=chunk('SM_CivicHallSmallDetails',.025)
rng=random.Random(220)
for wing,ys in enumerate([[-20,-15,-10],[44,49,54,59]]):
    for y in ys:
        for z in range(-55,90,6):
            if rng.random()<.16: continue
            x=92.7 if wing==0 else 95.2
            b.box((x,y,z),(.28,1.0,2.05),'DarkSteel')
            b.box((x-.17,y,z-1.12),(.85,1.30,.16),'Rust')
            if rng.random()<.22:
                b.box((x-.16,y,z+.03),(.06,.50,1.30),'Amber')
                b.box((x-.21,y,z+.03),(.075,.045,1.3),'DarkSteel')
for z in [-43,-17,11,48,78]:
    for y1,y2 in [(-22,-5),(10,31),(44,62)]:
        b.box((90.7,(y1+y2)/2,z), (2.5,y2-y1,.19),'Rust')
        b.tube((89.5,y1,z+1),(89.5,y2,z+1),.042,'DarkSteel',8)
        for y in range(math.ceil(y1),math.floor(y2),2): b.tube((89.5,y,z),(89.5,y,z+1),.03,'DarkSteel',6)
for y in [-19,-8,47,60]:
    b.tube((90.4,y,-58),(90.4,y,84),.14,'Rust',10)
    for z in range(-55,80,8):b.tube((90.4,y,z-.05),(90.4,y,z+.05),.23,'DarkSteel',10)

b=chunk('SM_DistantAccessBridges',.035)
# The player's route ends at the overlook; distant spans imply a larger connected ruin.
for start,end,z,width in [((24,8),(47,16),-1,3),((53,25),(92,31),-22,3.5),((53,22),(95,22),28,2.4),((68,31),(90,-6),-50,3)]:
    a=Vector((start[0],start[1],z)); c=Vector((end[0],end[1],z)); d=c-a; side=Vector((-d.y,d.x,0)).normalized(); yaw=math.atan2(d.y,d.x)
    b.box(tuple((a+c)/2+Vector((0,0,-.17))),(d.length,width,.34),'Concrete',yaw)
    for sg in [-1,1]:
        aa=a+side*sg*width/2; cc=c+side*sg*width/2
        b.tube(tuple(aa+Vector((0,0,1))),tuple(cc+Vector((0,0,1))),.055,'DarkSteel',8)
        b.tube(tuple(aa+Vector((0,0,-1.8))),tuple(cc+Vector((0,0,-1.8))),.11,'DarkSteel',8)
        n=max(3,int(d.length/3))
        for i in range(n+1):
            q=aa+(cc-aa)*(i/n); nxt=aa+(cc-aa)*(min(n,i+1)/n)
            b.tube(tuple(q),tuple(q+Vector((0,0,1))),.04,'Rust',8)
            b.tube(tuple(q+Vector((0,0,-1.8))),tuple(nxt),.065,'Rust',8)

# Closed cavern volume in the background, formed by rough patches with real depth.
for label,yc in [('Left',-70),('Center',10),('Right',90)]:
    b=chunk('SM_FarCavern_'+label)
    for iz,z in enumerate([-85,-40,5,50,95,138]):
        for iy in range(3):
            y=yc+(iy-1)*28
            b.rock((155+random.uniform(-4,4),y,z),(11,23,33),5100+iz*33+iy+int(yc*2),3)
b=chunk('SM_CavernCeiling')
for ix,x in enumerate([25,60,100,140]):
    for iy,y in enumerate([-40,5,50,95]): b.rock((x,y,125+random.uniform(-5,5)),(31,35,14),6200+ix*12+iy,3)
b=chunk('SM_SideCliffLower')
for i,z in enumerate([-15,-43,-72]):
    for j,x in enumerate([6,23,40]): b.rock((x,-13,z),(16,8,21),7000+i*12+j,3)

manifest={'generator':'build_environment.py','seed':1905,'blender_version':bpy.app.version_string,'source_units':'metres','source_axes':{'forward':'+X','right':'+Y','up':'+Z'},'fbx_axis_forward':'-Y','fbx_axis_up':'Z','fbx_unit_scale_factor':100,'all_object_transforms_identity':True,'uv_repeat_metres':1.5,'materials':MATERIAL_NAMES,'chunks':[],'anchors_m':{'player':[0,-.6,0],'companion':[7,0,0],'camera':[-5,1.5,2.0],'camera_target':[30,0,8],'near_pier':[50,22,0],'hall_center':[105,22,0]},'notes':['Geometry source authored in metres. UE world units are centimetres.','Import static meshes, combine meshes true per individual file, convert scene enabled, import uniform scale 1, convert scene unit enabled.','Blender native -Y/Z FBX metadata does not rotate authored mesh vertex coordinates; verify near-pier X/Y bounds after UE import before placing all chunks.','Every mesh pivot is the shared world origin. Place all actors at 0,0,0 with scale 1 and rotation 0.','UV0 is dominant-face world projection at 1.5 metres per repeat. Generate lightmap UVs only if baked lighting is later required.','Near rocks, bridge, metal bevels, modular real geometry. No baked background image.']}
previous=json.loads((ROOT/'environment_manifest.json').read_text()) if ROCKS_ONLY else None
changed=[]
for b in chunks:
    if ROCKS_ONLY and b.name not in ROCK_CHUNKS:
        manifest['chunks'].append(next(c for c in previous['chunks'] if c['name']==b.name))
    else:
        result=b.finish(); manifest['chunks'].append(result); changed.append(result['name'])
manifest['total_triangles']=sum(c['triangles'] for c in manifest['chunks'])
assert manifest['total_triangles'] < 1500000,manifest['total_triangles']
manifest['rock_refinement']={'method':'dense coherent multifrequency erosion, fracture grooves and smooth normals with hard fissures','per_rock_bounds_preserved':True,'changed_chunks':changed,'rock_triangles':sum(c['triangles'] for c in manifest['chunks'] if c['name'] in ROCK_CHUNKS)}
(ROOT/'environment_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('AshWell_RockRefinement_Source.blend' if ROCKS_ONLY else 'AshWell_Environment_Source.blend')))
print('DONE triangles=',manifest['total_triangles'],'chunks=',len(chunks),flush=True)
