"""Original distant maintenance crossing. Blender background generator only.
Source metre coordinates +X forward, +Y right, +Z up. All origins zero.
"""
import bpy,bmesh,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
ROOT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
NAMES=['Concrete','DarkSteel','Rust','Amber','Cloth']
MATS=[]
for name,color in zip(NAMES,[(.18,.18,.16,1),(.05,.055,.058,1),(.12,.07,.045,1),(1,.35,.055,1),(.033,.04,.039,1)]):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.72
 if name in ['Rust','DarkSteel']:p.inputs['Metallic'].default_value=.4
 if name=='Amber':p.inputs['Emission Color'].default_value=color;p.inputs['Emission Strength'].default_value=5
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

start=Vector((37,-12,-22));end=Vector((58,22,-22))
axis=(end-start).normalized();side=Vector((-axis.y,axis.x,0));up=Vector((0,0,1));length=(end-start).length
yaw=math.atan2(axis.y,axis.x)
bridge=Mesh('SM_DeepCrossing_Bridge',.008)
life=Mesh('SM_DeepCrossing_WorkersAndLamps',.003)
def pos(t,v=0,z=0):return start+(end-start)*t+side*v+up*z
# Narrow patched deck, readable but not a solid glowing strip.
count=58
for i in range(count):
 p=pos((i+.5)/count,0,-.075)
 bridge.box(tuple(p),(length/count-.012,1.8,.15),'DarkSteel' if i%7 in [0,1] else 'Concrete',yaw)
for sg in [-1,1]:
 bridge.beam(tuple(pos(0,sg*.87,-.17)),tuple(pos(1,sg*.87,-.17)),.12,.28,'Rust')
 bridge.beam(tuple(pos(0,sg*.87,-2)),tuple(pos(1,sg*.87,-2)),.13,.16,'DarkSteel')
 for z,rad in [(1,.034),(.46,.022)]:bridge.tube(tuple(pos(0,sg*.88,z)),tuple(pos(1,sg*.88,z)),rad,'Rust',10)
 for i in range(25):
  p=pos(i/24,sg*.88,0);bridge.tube(tuple(p),tuple(p+up*1.04),.029,'DarkSteel',8)
 for i in range(14):
  t=i/13;bridge.beam(tuple(pos(t,sg*.87,-.18)),tuple(pos(t,sg*.87,-2)),.095,.10,'Rust')
  if i<13:
   bridge.beam(tuple(pos(t,sg*.87,-2)),tuple(pos((i+1)/13,sg*.87,-.18)),.08,.095,'DarkSteel')
for i in range(14):
 t=i/13;bridge.beam(tuple(pos(t,-.9,-.18)),tuple(pos(t,.9,-.18)),.12,.15,'DarkSteel')
# End mounting blocks are small structural ties, not another giant pedestal.
for t in [0,1]:
 bridge.box(tuple(pos(t,0,-.24)),(.65,2.16,.32),'Concrete',yaw)
 for v in [-.87,.87]:bridge.box(tuple(pos(t,v,-.11)),(.42,.32,.08),'Rust',yaw)

def ellipsoid(builder,c,size,mat,detail=2):
 bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=detail,radius=1)
 bm.verts.ensure_lookup_table();bm.verts.index_update();c=Vector(c)
 verts=[tuple(c+axis*(v.co.x*size[0])+side*(v.co.y*size[1])+up*(v.co.z*size[2])) for v in bm.verts]
 faces=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free();builder.add(verts,faces,mat)
workers=[]
for wi,t in enumerate([.3,.7]):
 center=pos(t,-.17 if wi==0 else .32,0);direction=1 if wi==0 else -1
 def q(x,y,z):return center+axis*(x*direction)+side*y+up*z
 # Coarse coat silhouette with separate boots, legs, shoulders and helmet.
 for y,x in [(-.115,-.035),(.115,.045)]:
  life.box(tuple(q(x+.045,y,.075)),(.30,.16,.15),'DarkSteel',yaw)
  life.tube(tuple(q(x,y,.15)),tuple(q(0,y,.74)),.075,'Cloth',10,.092)
 life.tube(tuple(q(0,0,.54)),tuple(q(-.025,0,1.12)),.255,'Cloth',14,.20)
 ellipsoid(life,q(-.015,0,1.23),(.145,.235,.21),'Cloth',2)
 life.tube(tuple(q(-.015,0,1.37)),tuple(q(-.015,0,1.46)),.074,'Cloth',10)
 ellipsoid(life,q(-.008,0,1.535),(.11,.105,.135),'DarkSteel',2)
 ellipsoid(life,q(-.008,0,1.625),(.14,.13,.075),'Rust',2)
 life.tube(tuple(q(-.008,0,1.587)),tuple(q(-.008,0,1.609)),.151,'DarkSteel',12)
 # One worker carries a bag; the second rests a forearm toward the rail.
 for sy in [-1,1]:
  shoulder=q(0,sy*.24,1.26)
  elbow=q(.07,sy*.275,1.01) if wi==0 else q(.08,sy*.31,1.10)
  wrist=q(.04,sy*.26,.82) if wi==0 else q(.24,sy*.36,1.0)
  life.tube(tuple(shoulder),tuple(elbow),.071,'Cloth',10,.06)
  life.tube(tuple(elbow),tuple(wrist),.06,'Cloth',10,.046)
  ellipsoid(life,wrist,(.055,.046,.06),'DarkSteel',1)
 life.box(tuple(q(-.17,0,1.1)),(.19,.34,.38),'Cloth',yaw)
 workers.append({'id':'worker_'+str(wi+1),'feet_source_m':list(center),'height_m':1.7,'station_fraction':t})
anchors=[]
for i,t in enumerate([.17,.5,.83]):
 base=pos(t,.87,0);anchor=pos(t,.68,1.22)
 life.tube(tuple(base),tuple(base+up*1.54),.039,'Rust',10)
 life.tube(tuple(base+up*1.5),tuple(anchor+up*.28),.028,'DarkSteel',8)
 life.tube(tuple(anchor-up*.115),tuple(anchor+up*.115),.081,'Amber',12)
 life.tube(tuple(anchor-up*.15),tuple(anchor-up*.11),.107,'DarkSteel',12)
 life.tube(tuple(anchor+up*.11),tuple(anchor+up*.16),.115,'DarkSteel',12,.075)
 for j in range(4):
  a=j*math.tau/4;v=axis*(math.cos(a)*.086)+side*(math.sin(a)*.086)
  life.tube(tuple(anchor+v-up*.13),tuple(anchor+v+up*.13),.009,'DarkSteel',6)
 anchors.append({'name':'DeepCrossingLamp_'+str(i+1),'source_m':list(anchor),'suggested_unreal_intensity_lumens':300,'suggested_attenuation_radius_cm':450,'suggested_color_srgb':[1,.48,.16]})
entries=[bridge.finish(),life.finish()]
assert sum(e['triangles'] for e in entries)<70000
for e in entries:e['sha256']=hashlib.sha256((ROOT/e['file']).read_bytes()).hexdigest()
manifest={'generator':'build_deep_crossing.py','authorship':'Original procedural geometry for Ash Well; no downloaded mesh or purchased assets.','license':'CC0-1.0',
 'source_units':'metres','source_axes':'+X forward, +Y right, +Z up','start_m':list(start),'end_m':list(end),'width_m':1.8,'rail_height_m':1.0,'under_truss_depth_m':2.0,
 'source_origins':[0,0,0],'fbx_export':{'axis_forward':'-Y','axis_up':'Z','apply_scale_options':'FBX_SCALE_UNITS','apply_unit_scale':True},
 'parent_import':'Place both meshes at world origin. Parent handles Y mirror, UE lights, material binding and visibility.','material_slots':NAMES,
 'assets':entries,'workers':workers,'light_anchors':anchors,'total_triangles':sum(e['triangles'] for e in entries)}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'DeepCrossing_Source.blend'))
print('COMPLETE',json.dumps({'triangles':manifest['total_triangles'],'lights':anchors}),flush=True)
