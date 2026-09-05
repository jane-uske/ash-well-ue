"""Original procedural industrial-gothic architecture for Ash Well.
Blender background generator. All coordinates: metres, X forward, Y right, Z up.
Run Blender --background --python build_architecture_v2.py.
This is genuine geometry with open arcades and rooms, not a facade image.
"""
import bpy,bmesh,math,random,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ROOT.mkdir(parents=True,exist_ok=True)
random.seed(190503)
SERVICE_ONLY='--service-only' in sys.argv
SERVICE_FILES={'SM_AV2_ServiceRooms_0','SM_AV2_ServiceRooms_1','SM_AV2_ServiceRooms_2','SM_AV2_Windows_And_Lamps'}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
NAMES=['Rock','Rust','Concrete','DarkSteel','Amber','Cloth']
MATS=[]
for name,color in zip(NAMES,[(.09,.10,.11,1),(.18,.075,.03,1),(.20,.20,.18,1),(.045,.05,.055,1),(1,.32,.055,1),(.045,.055,.05,1)]):
    m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not p:
        p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.78
    if name in ['Rust','DarkSteel']:p.inputs['Metallic'].default_value=.65
    if name=='Amber':p.inputs['Emission Color'].default_value=color;p.inputs['Emission Strength'].default_value=2
    MATS.append(m)

class Mesh:
    def __init__(self,name,bevel=.015):self.name=name;self.v=[];self.f=[];self.m=[];self.bevel=bevel
    def add(self,v,f,mat):
        k=len(self.v);self.v.extend(v);self.f.extend(tuple(k+i for i in face) for face in f);self.m.extend([NAMES.index(mat)]*len(f))
    def box(self,c,s,mat='DarkSteel',yaw=0):
        c=Vector(c);co=math.cos(yaw);si=math.sin(yaw);v=[]
        for z in [-1,1]:
            for y in [-1,1]:
                for x in [-1,1]:
                    dx=x*s[0]/2;dy=y*s[1]/2;v.append(tuple(c+Vector((dx*co-dy*si,dx*si+dy*co,z*s[2]/2))))
        self.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat)
    def beam(self,a,b,w=.15,d=None,mat='DarkSteel'):
        a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u).normalized();d=w if d is None else d
        pts=[tuple(p+u*x*w/2+v*y*d/2) for p in [a,b] for y in [-1,1] for x in [-1,1]]
        self.add(pts,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat)
    def tube(self,a,b,r=.08,mat='DarkSteel',n=12,r2=None):
        a=Vector(a);b=Vector(b)
        if (b-a).length<1e-6:return
        axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u).normalized();verts=[]
        for p,rad in [(a,r),(b,r if r2 is None else r2)]:
            for i in range(n):
                t=i*math.tau/n;verts.append(tuple(p+rad*(u*math.cos(t)+v*math.sin(t))))
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(verts,faces,mat)
    def line(self,points,r=.04,mat='DarkSteel',n=8):
        for a,b in zip(points,points[1:]):self.tube(a,b,r,mat,n)
    def ring(self,c,r,minor,mat='Rust',segments=64,sides=8,axis='Z',start=0,end=math.tau):
        c=Vector(c);verts=[]
        normal=Vector((0,0,1)) if axis=='Z' else Vector((1,0,0))
        u=Vector((1,0,0)) if axis=='Z' else Vector((0,1,0));v=normal.cross(u)
        for i in range(segments+1):
            t=start+(end-start)*i/segments;radial=u*math.cos(t)+v*math.sin(t)
            for j in range(sides):
                q=j*math.tau/sides;verts.append(tuple(c+radial*(r+minor*math.cos(q))+normal*minor*math.sin(q)))
        faces=[]
        for i in range(segments):
            for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
        self.add(verts,faces,mat)
    def arch(self,x,y,z,width,height,thick=.7,depth=1.5,mat='Concrete',segments=32):
        # Two cubic Bezier branches form a pointed structural arch.
        h=width/2
        left=[Vector((-h,0)),Vector((-h,height*.54)),Vector((-h*.47,height*.86)),Vector((0,height))]
        right=[Vector((0,height)),Vector((h*.47,height*.86)),Vector((h,height*.54)),Vector((h,0))]
        pts=[]
        for controls in [left,right]:
            for i in range(segments//2):
                t=i/(segments//2);pts.append(controls[0]*(1-t)**3+controls[1]*3*(1-t)**2*t+controls[2]*3*(1-t)*t*t+controls[3]*t**3)
        pts.append(right[-1])
        for i in range(len(pts)-1):
            a=pts[i];b=pts[i+1];tan=(b-a).normalized();out=Vector((-tan.y,tan.x))
            va=a+out*thick/2;vb=b+out*thick/2;vc=b-out*thick/2;vd=a-out*thick/2
            verts=[(xx,y+p.x,z+p.y) for xx in [x-depth/2,x+depth/2] for p in [va,vb,vc,vd]]
            self.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
    def ladder(self,x,y,z0,z1,width=.65):
        for yy in [y-width/2,y+width/2]:self.tube((x,yy,z0),(x,yy,z1),.04,'Rust',8)
        for i in range(int((z1-z0)/.38)+1):
            z=z0+i*.38;self.tube((x,y-width/2,z),(x,y+width/2,z),.027,'DarkSteel',8)
        for z in range(math.ceil(z0),math.floor(z1),3):
            for yy in [y-width/2,y+width/2]:self.beam((x,yy,z),(x+.35,yy,z),.07,.06,'DarkSteel')
    def rail(self,a,b,height=1.05):
        a=Vector(a);b=Vector(b);d=b-a;count=max(1,math.ceil(d.length/1.8))
        for z in [height,.46]:self.tube(tuple(a+Vector((0,0,z))),tuple(b+Vector((0,0,z))),.037 if z==height else .025,'Rust',8)
        for i in range(count+1):
            p=a+d*i/count;self.tube(tuple(p),tuple(p+Vector((0,0,height))),.03,'DarkSteel',8)
    def flange(self,p,axis,r):
        p=Vector(p);axis=Vector(axis).normalized();self.tube(tuple(p-axis*.07),tuple(p+axis*.07),r*1.38,'Rust',16)
        u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u)
        for i in range(8):
            t=i*math.tau/8;q=p+(u*math.cos(t)+v*math.sin(t))*r*1.13
            self.tube(tuple(q-axis*.105),tuple(q+axis*.105),min(.047,r*.13),'DarkSteel',6)
    def finish(self):
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        obj=bpy.data.objects.new(self.name,mesh);bpy.context.collection.objects.link(obj)
        for m in MATS:mesh.materials.append(m)
        for p,mi in zip(mesh.polygons,self.m):p.material_index=mi
        bpy.context.view_layer.objects.active=obj;obj.select_set(True)
        if self.bevel:
            mod=obj.modifiers.new('Edge wear bevel','BEVEL');mod.width=self.bevel;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.65
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.dissolve_degenerate(bm,dist=.000001,edges=list(bm.edges))
        tiny=[f for f in bm.faces if f.calc_area()<1e-10]
        if tiny:bmesh.ops.delete(bm,geom=tiny,context='FACES_ONLY')
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        for f in bm.faces:f.smooth=True
        for e in bm.edges:
            if len(e.link_faces)==2:e.smooth=e.calc_face_angle(0)<math.radians(40)
        bm.to_mesh(obj.data);bm.free();mesh=obj.data;mesh.update()
        uv=mesh.uv_layers.new(name='UVMap')
        for p in mesh.polygons:
            axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
            for li in p.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]/1.5,co[axes[1]]/1.5)
        mesh.calc_loop_triangles();co=[v.co for v in mesh.vertices]
        bounds={a:[round(fn(v[k] for v in co),5) for k in range(3)] for a,fn in [('min',min),('max',max)]}
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
        bpy.ops.export_scene.fbx(filepath=str(ROOT/(self.name+'.fbx')),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,mesh_smooth_type='EDGE',use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=False)
        obj.select_set(False);result={'name':self.name,'file':self.name+'.fbx','triangles':len(mesh.loop_triangles),'vertices':len(mesh.vertices),'bounds_m':bounds,'origin_m':[0,0,0],'material_slots':NAMES}
        print('EXPORTED '+json.dumps(result),flush=True);return result

chunks=[]
def new(name,bevel=.015):
    o=Mesh('SM_AV2_'+name,bevel);chunks.append(o);return o

# THE NEAR PIER: a believable vertical machine/structure, divided into service tiers.
cx,cy=55,27
b=new('Pier_Core',.075)
for level in range(12):
    z=-80+level*16;r=6.4-level*.095
    b.tube((cx,cy,z),(cx,cy,z+15.9),r,'Concrete',32,r-.065)
    for dz,extra,h in [(0,.65,.60),(.85,.37,.30),(15.35,.28,.20)]:
        b.tube((cx,cy,z+dz),(cx,cy,z+dz+h),r+extra,'Rust',32)
    for i in range(16):
        a=i*math.tau/16;rr=r+.05
        b.box((cx+rr*math.cos(a),cy+rr*math.sin(a),z+8),(.24,.54,12.8),'Concrete',a)
b=new('Pier_Exoskeleton',.025)
for i in range(16):
    a=i*math.tau/16;r=6.55;xx=cx+r*math.cos(a);yy=cy+r*math.sin(a)
    b.box((xx,yy,16),(.28,.45,188),'DarkSteel',a)
    for z in range(-77,110,8):
        b.box((xx,yy,z),(.48,.82,.42),'Rust',a)
        b.box((xx+math.cos(a)*.16,yy+math.sin(a)*.16,z),(.17,.49,.66),'DarkSteel',a)
    # Two slim flanking ribs give a layered profile and shadow channels.
    for da in [-.043,.043]:
        rr=6.62;b.tube((cx+rr*math.cos(a+da),cy+rr*math.sin(a+da),-78),(cx+rr*math.cos(a+da),cy+rr*math.sin(a+da),110),.065,'Rust',8)
b=new('Pier_Galleries',.015)
for z in [-64,-32,0,32,64,96]:
    for i in range(40):
        a=i*math.tau/40;aa=(i+.5)*math.tau/40;rr=7.03
        b.box((cx+rr*math.cos(aa),cy+rr*math.sin(aa),z),(.85,1.17,.18),'DarkSteel',aa)
        p=Vector((cx+7.52*math.cos(a),cy+7.52*math.sin(a),z+.08));q=Vector((cx+7.52*math.cos(a+math.tau/40),cy+7.52*math.sin(a+math.tau/40),z+.08))
        b.rail(tuple(p),tuple(q))
        if i%2==0:b.beam((cx+6.30*math.cos(a),cy+6.30*math.sin(a),z-2.5),tuple(p),.10,.13,'Rust')
b=new('Pier_DoorsLadders',.01)
light=new('Windows_And_Lamps',.008)
for j,(a,z0,z1) in enumerate([(math.pi,-78,-33),(math.pi*.92,-31,31),(math.pi*1.04,33,95)]):
    x=cx+7.18*math.cos(a);y=cy+7.18*math.sin(a);b.ladder(x,y,z0,z1,.70)
for z in [-63,-47,-31,-15,1,17,33,49,65,81,97]:
    for a in [math.pi*.88,math.pi*1.13,math.pi*1.5]:
        r=6.47;p=Vector((cx+r*math.cos(a),cy+r*math.sin(a),z+1.50));yaw=a
        b.box(tuple(p),(.18,1.15,2.40),'DarkSteel',yaw)
        for dy in [-.68,.68]:b.box(tuple(p+Vector((-math.sin(a)*dy,math.cos(a)*dy,0))),(.36,.16,2.85),'Rust',yaw)
        b.box(tuple(p+Vector((0,0,1.44))),(.40,1.5,.18),'Rust',yaw)
        b.box(tuple(p+Vector((math.cos(a)*.12,math.sin(a)*.12,.33))),(.20,.68,.70),'DarkSteel',yaw)
        if random.random()<.29:light.box(tuple(p+Vector((math.cos(a)*.24,math.sin(a)*.24,.36))),(.035,.46,.50),'Amber',yaw)
        b.tube(tuple(p+Vector((math.cos(a)*.22,math.sin(a)*.22,-.18))),tuple(p+Vector((math.cos(a)*.35,math.sin(a)*.35,-.18))),.09,'Rust',8)

# HALL: three genuine open storeys. A pair of setback colonnades can be seen through.
ys=[-36,-12,12,36]
b=new('Hall_Piers_Front',.055)
for y in ys:
    b.box((90,y,22),(5.1,3.6,177),'Concrete')
    b.box((86.85,y,22),(.75,1.05,177),'DarkSteel')
    for sy in [-1.25,1.25]:
        b.tube((87.25,y+sy,-65),(87.25,y+sy,110),.34,'Concrete',12)
        b.tube((86.78,y+sy,-65),(86.78,y+sy,110),.065,'Rust',8)
    for z in [-65,-32,4,39,74,108]:
        for dz,size in [(0,(6.8,5.7,.75)),(.65,(6.1,5.0,.45)),(1.1,(5.5,4.4,.30))]:b.box((89.8,y,z+dz),size,'Concrete')
        b.box((86.6,y,z+2),(.35,4.9,.55),'Rust')
        for yy in [-1.5,-.75,0,.75,1.5]:b.box((86.34,y+yy,z+2.05),(.10,.13,.25),'DarkSteel')
b=new('Hall_Piers_Interior',.05)
for x in [102,114]:
    for y in ys:
        b.box((x,y,24),(2.3,2.3,172),'Concrete')
        for z in [-64,-30,4,39,74,109]:
            b.box((x,y,z),(4.0,3.8,.8),'Concrete');b.box((x,y,z+.65),(3.1,3.1,.5),'DarkSteel')
for li,(base,h) in enumerate([(-29,27),(6,27),(41,27),(76,27)]):
    b=new('Hall_Arcades_'+str(li),.022)
    for yy in [-24,0,24]:
        for xx,thick,depth in [(89.4,1.10,2.1),(101.9,.72,1.2),(113.7,.62,.85)]:
            b.arch(xx,yy,base,20.8,h,thick,depth,'Concrete',40)
        # Multiple nested mouldings add depth rather than outlining a wall.
        for xx,w,hh,th in [(88.20,22.0,h+.40,.25),(87.93,22.75,h+.70,.20),(90.15,19.40,h-.85,.35)]:b.arch(xx,yy,base,w,hh,th,.34,'Rust' if xx<88 else 'Concrete',40)
        for sg in [-1,1]:
            y=yy+sg*10.4
            b.tube((88.5,y,base-3),(88.5,y,base+2),.37,'Concrete',12)
            b.box((88.55,y,base-.55),(1.4,1.5,.4),'Concrete')
        # Small boss at pointed apex, with a projecting iron anchor.
        b.box((88.1,yy,base+h),(.45,1.30,1.7),'Concrete')
        b.box((87.75,yy,base+h-.2),(.25,.43,.75),'DarkSteel')
b=new('Hall_TransverseVaults',.02)
for z in [-29,6,41,76]:
    for y in ys:
        # Ribs connecting front and rear colonnades, with real cross-depth spans.
        for j in range(24):
            t=j/24;u=(j+1)/24
            a=(90+24*t,y,z+20+5*math.sin(t*math.pi));c=(90+24*u,y,z+20+5*math.sin(u*math.pi))
            b.beam(a,c,.38,.54,'Concrete')
    for y in [-24,0,24]:
        for j in range(28):
            t=j/28;u=(j+1)/28
            b.tube((89+25*t,y-8+16*t,z+22+4*math.sin(t*math.pi)),(89+25*u,y-8+16*u,z+22+4*math.sin(u*math.pi)),.14,'DarkSteel',10)
            b.tube((89+25*t,y+8-16*t,z+22+4*math.sin(t*math.pi)),(89+25*u,y+8-16*u,z+22+4*math.sin(u*math.pi)),.14,'DarkSteel',10)

b=new('Hall_FloorEdges_And_Galleries',.018)
for z in [-65,-32,3,38,73,108]:
    # U-shaped floors leave the inner hall open from above and from the front.
    b.box((101,-34,z),(24,4,.55),'Concrete');b.box((101,34,z),(24,4,.55),'Concrete')
    b.box((113.5,0,z),(3,72,.55),'Concrete')
    b.box((90,0,z),(4.2,72,.65),'Concrete')
    for x in [87.9,91.9,111.8]:b.box((x,0,z+.2),(.20,73,.48),'Rust')
    b.rail((87.7,-35,z+.35),(87.7,35,z+.35))
    b.rail((92.2,-34,z+.35),(92.2,34,z+.35))
    # Visible braces stop it reading as floating decorative lines.
    for y in range(-34,36,4):b.beam((92,y,z-3.0),(87.9,y,z-.3),.17,.24,'DarkSteel')
for z in [9,15,44,50,80,86]:
    # Asymmetric service balconies occupy selected sides, not every bay.
    y0,y1=(-35,-13) if z%2 else (13,35)
    b.box((91.9,(y0+y1)/2,z),(3.9,y1-y0,.22),'Rust');b.rail((89.8,y0,z+.15),(89.8,y1,z+.15))

# Habitation/service inserts: separate shells form deep rectangular window holes.
# Rooms occupy partial spans, keeping each great arch visibly open.
def room(shell,x,y,z,width=3.4,lit=False,rng=None):
    height=3.65;opening=1.85 if rng.random()<.55 else 2.20;oh=2.05;depth=2.5;sill=.62
    # side piers, lintel and sill leave a genuine aperture through the front wall.
    side=(width-opening)/2
    shell.box((x,y-(opening+side)/2,z+height/2),(.45,side,height),'Concrete')
    shell.box((x,y+(opening+side)/2,z+height/2),(.45,side,height),'Concrete')
    shell.box((x,y,z+sill/2),(.45,opening,sill),'Concrete')
    shell.box((x,y,z+(height+(sill+oh))/2),(.45,opening,height-(sill+oh)),'Concrete')
    # The window recess has side reveals and a dark interior wall set back 2.5 m.
    shell.box((x+depth/2,y-width/2,z+height/2),(depth,.16,height),'Concrete')
    shell.box((x+depth/2,y+width/2,z+height/2),(depth,.16,height),'Concrete')
    shell.box((x+depth,y,z+height/2),(.20,width,height),'DarkSteel')
    shell.box((x+depth/2,y,z),(depth,width,.16),'Concrete')
    shell.box((x-.32,y,z+sill-.04),(.75,opening+.48,.18),'Rust')
    for yy in [y-opening/2-.08,y+opening/2+.08]:shell.box((x-.29,yy,z+sill+oh/2),(.17,.12,oh+.23),'DarkSteel')
    shell.box((x-.29,y,z+sill+oh+.08),(.17,opening+.28,.14),'Rust')
    # Dense but human-scale mullions and dark recesses replace blank square boxes.
    rng.random() # keep variation deterministic relative to the earlier generator
    for dy in [-opening/6,opening/6]:shell.box((x-.34,y+dy,z+sill+oh/2),(.10,.064,oh),'DarkSteel')
    shell.box((x-.35,y,z+sill+oh*.52),(.12,opening,.065),'DarkSteel')
    for zz in [z+.20,z+height-.18]:shell.box((x-.26,y,zz),(.12,width-.10,.11),'Rust')
    shell.box((x+1.00,y,z+sill+oh/2),(.025,opening*.97,oh*.98),'DarkSteel')
    if lit:
        for dy in [-.28,.28]:light.box((x+.85,y+dy,z+sill+1.04),(.025,.25,.80),'Amber')
        shell.box((x+.82,y,z+sill+1.04),(.04,.065,.84),'DarkSteel')
    if rng.random()<.35:shell.box((x-.40,y+.85,z+1.3),(.32,.43,.72),'DarkSteel')

for group,(y0,x0,count) in enumerate([(-33,94.0,7),(-9,97.0,6),(14,95.3,6)]):
    b=new('ServiceRooms_'+str(group),.02);rng=random.Random(317+group)
    floors=[-26,-22,-18,-14,-10,-6,-2,4,8,12,16,20,24]
    for floor,z in enumerate(floors):
        # Irregular gaps retain the giant open arcade behind the service layers.
        for col in range(count):
            if rng.random()<(.22 if z>0 else .15):continue
            yy=y0+col*3.5;xx=x0+(floor%3)*.48
            room(b,xx,yy,z,3.38,rng.random()<.12,rng)
        # Every row has a visible continuous gallery and end struts into the piers.
        center_y=y0+(count-1)*1.75;ylo=y0-1.85;yhi=y0+(count-1)*3.5+1.85
        b.box((x0-.35,center_y,z-.10),(3.3,yhi-ylo,.22),'DarkSteel')
        b.box((x0-2.02,center_y,z-.07),(.16,yhi-ylo,.36),'Rust')
        b.rail((x0-2.10,ylo,z+.06),(x0-2.10,yhi,z+.06))
        for yy in [ylo+.3,yhi-.3]:
            b.beam((x0+1.2,yy,z-3.2),(x0-1.85,yy,z-.22),.12,.17,'Rust')
            b.beam((x0+1.2,yy,z-3.2),(x0+1.2,yy,z-.22),.14,.18,'DarkSteel')
        if z in [4,12,20]:
            # Short flights connect alternate four-metre gallery levels.
            sx=x0-1.25;sy=ylo+.8
            for step in range(16):b.box((sx,sy+step*.275,z+.12+(step+1)*.25),(1.1,.30,.12),'Rust')
            for dx in [-.57,.57]:
                b.beam((sx+dx,sy,z),(sx+dx,sy+4.25,z+4),.07,.12,'DarkSteel')
                b.rail((sx+dx,sy,z+.15),(sx+dx,sy+4.25,z+4.15),.85)

b=new('VerticalPipes_And_Valves',.008)
for i,y in enumerate([-34,-31,-13,-10,10,14,31,34]):
    x=86.2+(i%3)*.26;r=[.16,.095,.24][i%3]
    b.tube((x,y,-62),(x,y,105),r,'Rust',12)
    for z in range(-58,104,6):
        b.flange((x,y,z),(0,0,1),r)
        b.beam((x,y,z+.5),(90,y,z+.5),.075,.09,'DarkSteel')
    for z in [-23,13,54]:
        # curved elbow and short branch feed each maintenance level.
        pts=[(x-.8*math.sin(t*math.pi/2),y,z+.8*(1-math.cos(t*math.pi/2))) for t in [j/12 for j in range(13)]]
        b.line(pts,r,'Rust',12);b.flange(pts[-1],(-1,0,0),r)
        b.ring((x-1.0,y,z+.85),r*.95,.022,'DarkSteel',16,6,'X')
b=new('Ladders_And_Switchgear',.008)
for x,y,z0,z1 in [(92,-33,-26,4),(92,-14,5,38),(92,14,40,73),(92,33,74,107),(112,8,-29,3)]:
    b.ladder(x,y,z0,z1,.68)
    for z in range(math.ceil(z0+2),int(z1),4):
        b.ring((x-.02,y,z),.51,.025,'Rust',20,6,'Z',math.pi*.15,math.pi*1.85)
for x,y,z in [(88,-32,-3),(88,-15,4),(89,17,3),(89,32,38),(92,3,-27)]:
    b.box((x,y,z+1.3),(.45,1.10,1.55),'DarkSteel');b.box((x-.26,y,z+1.3),(.08,.98,1.4),'Rust')
    for zz in [z+.85,z+1.30,z+1.75]:
        for yy in [-.26,.12]:b.tube((x-.33,y+yy,zz),(x-.40,y+yy,zz),.06,'DarkSteel',8)
    b.box((x-.35,y+.37,z+1.3),(.08,.055,.39),'DarkSteel')

# LOWER ENGINE HALL: great flywheels, turbine housings, pressure tanks and piers.
b=new('LowerFoundations',.07)
for y in [-31,-8,16,34]:
    b.box((96,y,-52),(9,6,30),'Concrete');b.box((96,y,-67),(15,10,1.8),'Concrete')
    for sy in [-3.0,3.0]:b.beam((86,y+sy,-57),(94,y+sy,-33),.95,1.3,'Concrete')
for z in [-65,-47,-32]:
    b.box((106,0,z),(22,73,.70),'Concrete');b.box((94.7,0,z+.10),(.65,73,.55),'DarkSteel')
b=new('LowerMachinery',.02)
for idx,(x,y,z,r) in enumerate([(97,-21,-44,5.7),(97,3,-46,7.2),(100,25,-48,4.8)]):
    b.tube((x+1.0,y,z),(x+7.2,y,z),r*.88,'DarkSteel',48)
    for xx in [x,x+1,x+6.6]:
        b.ring((xx,y,z),r,.28,'Rust',64,10,'X')
        b.ring((xx-.12,y,z),r*.79,.14,'DarkSteel',64,8,'X')
    b.tube((x-.3,y,z),(x+7.5,y,z),r*.20,'Rust',32)
    for j in range(12):
        t=j*math.tau/12;a=(x-.22,y+math.cos(t)*r*.23,z+math.sin(t)*r*.23);c=(x-.22,y+math.cos(t)*r*.82,z+math.sin(t)*r*.82)
        b.beam(a,c,.22,.48,'DarkSteel')
    for j in range(48):
        t=j*math.tau/48;yy=y+math.cos(t)*r;zz=z+math.sin(t)*r
        b.box((x-.12,yy,zz),(.65,.25,.25),'Rust')
    for sy in [-r*.65,r*.65]:b.box((x+3,y+sy,z-r-1.5),(8,1.7,2.5),'Concrete')
for y in [-31,-12,13,32]:
    b.tube((108,y,-62),(108,y,-35),1.18,'DarkSteel',24)
    for z in [-60,-55,-50,-45,-40,-36]:b.flange((108,y,z),(0,0,1),1.18)
    b.tube((106,y,-36),(113,y,-36),.42,'Rust',16)

b=new('DeepBridges_And_SuspendedWalks',.016)
def bridge(start,end,width=2.7,truss=3):
    a=Vector(start);c=Vector(end);d=c-a;side=Vector((-d.y,d.x,0)).normalized();yaw=math.atan2(d.y,d.x)
    b.box(tuple((a+c)/2-Vector((0,0,.18))),(d.length,width,.36),'Concrete',yaw)
    steps=math.ceil(d.length/3)
    for sg in [-1,1]:
        aa=a+side*sg*width/2;cc=c+side*sg*width/2;b.rail(tuple(aa),tuple(cc))
        b.beam(tuple(aa-Vector((0,0,truss))),tuple(cc-Vector((0,0,truss))),.18,.27,'DarkSteel')
        b.beam(tuple(aa-Vector((0,0,.3))),tuple(cc-Vector((0,0,.3))),.16,.28,'Rust')
        for i in range(steps):
            q=aa+(cc-aa)*i/steps;r=aa+(cc-aa)*(i+1)/steps
            b.beam(tuple(q-Vector((0,0,truss))),tuple(r),.12,.17,'DarkSteel')
            b.beam(tuple(q),tuple(q-Vector((0,0,truss))),.13,.20,'Rust')
            b.beam(tuple(q-side*width/2),tuple(q+side*width/2),.10,.15,'DarkSteel')
bridge((24,8,0),(49,23,0),3.0,2.4)
bridge((57,33,-32),(90,34,-32),2.5,3.0)
bridge((57,29,32),(90,12,32),2.5,2.8)
bridge((52,25,-64),(95,-12,-64),3.2,3.5)
bridge((88,-35,3),(70,-48,3),2.2,2.0)

b=new('DrapedCables',0)
for i,(start,end,sag,r) in enumerate([((87,-31,32),(55,21,32),4.0,.046),((87,-29,35),(55,20,34),5.8,.028),((90,31,69),(57,30,69),7.3,.04),((89,27,64),(55,25,64),8,.06),((90,-28,-22),(89,30,-22),3.5,.034),((91,-28,14),(92,26,14),2.2,.025)]):
    a=Vector(start);c=Vector(end);pts=[]
    for j in range(61):t=j/60;pts.append(tuple(a+(c-a)*t-Vector((0,0,sag*4*t*(1-t)))))
    b.line(pts,r,'DarkSteel',8)
for y in [-29,-11,15,33]:
    pts=[(87.8+.3*math.sin(j*.12),y+.3*math.cos(j*.11),100-j*2) for j in range(85)]
    b.line(pts,.034,'DarkSteel',8)

# Recessed upper chambers: small paired lancets retain dark apertures behind the ribs.
b=new('UpperClerestory',.025)
for y in [-29,-19,-5,5,19,29]:
    x=107.5;z=86
    b.box((x+3,y,z+8),(5.8,5.6,.40),'Concrete');b.box((x+3,y-2.7,z),(5.8,.35,16),'Concrete');b.box((x+3,y+2.7,z),(5.8,.35,16),'Concrete')
    for yy in [y-.95,y+.95]:
        for sg in [-1,1]:b.box((x,yy+sg*.72,z-1.8),(.6,.32,9.0),'Concrete')
        b.arch(x,yy,z+2.7,1.45,3.6,.35,.75,'Concrete',20)
        b.arch(x-.37,yy,z+2.7,1.60,3.75,.09,.15,'Rust',20)
    b.box((x+5.5,y,z),(0.25,5.4,15),'DarkSteel')

manifest={'version':2,'generator':'build_architecture_v2.py','blender_version':bpy.app.version_string,'original_geometry':True,'source_units':'metres','axes':{'forward':'+X','right':'+Y','up':'+Z'},'fbx_axis_forward':'-Y','fbx_axis_up':'Z','fbx_unit_scale_factor':100,'ue_actor_scale_after_import':[1,-1,1],'uv_repeat_metres':1.5,'material_slots':NAMES,'chunks':[],'replace_old_prefixes':['SM_ColossalPier','SM_CivicHall','SM_DistantAccessBridges'],'anchors_m':{'pier_center':[55,27,0],'hall_front':[89,0,0],'hall_rear':[114,0,0],'bridge_start':[24,8,0]},'design':['Open front and rear arcades separated by 24m, with no full facade backing wall.','Actual hollow room shells with recessed lights and paired upper lancet openings.','Tiered near pier with projecting galleries, human-scale ladders, pipe clamps and maintenance doors.','Large flywheels and pressure machinery under lower platforms.','Shared pivot origin; imported UE actor mirror Y restores the verified source convention.']}
previous=json.loads((ROOT/'architecture_v2_manifest.json').read_text()) if SERVICE_ONLY else None
for chunk in chunks:
    if SERVICE_ONLY and chunk.name not in SERVICE_FILES:
        manifest['chunks'].append(next(c for c in previous['chunks'] if c['name']==chunk.name))
    else:manifest['chunks'].append(chunk.finish())
manifest['triangles']=sum(c['triangles'] for c in manifest['chunks'])
assert manifest['triangles']<3000000,manifest['triangles']
manifest['service_revision']={'version':2,'changed_files':sorted(SERVICE_FILES),'new_gallery_levels_m':[4,8,12,16,20,24],'window_light_size_m':[.025,.25,.80],'description':'Human-scale multi-pane dark recessed windows, supported galleries and stairs; no floating room shells.'}
(ROOT/'architecture_v2_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('ServiceRefinement_Source.blend' if SERVICE_ONLY else 'ArchitectureV2_Source.blend')))
print('DONE',len(chunks),'CHUNKS',manifest['triangles'],'TRIANGLES',flush=True)
