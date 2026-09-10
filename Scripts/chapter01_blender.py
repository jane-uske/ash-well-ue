"""Original centimetre-scale modular Chapter One kit, executed through Blender MCP.
Create a separate scene and .blend library; never replace the user's open blend file.
"""
import bpy,math,json,bmesh
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'SourceAssets/Chapter01';OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.data.scenes.new('AW_Chapter01_Kit');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
colors={'Steel':(.105,.13,.145,1),'Rust':(.28,.12,.045,1),'Stone':(.29,.28,.25,1),'Cloth':(.21,.16,.09,1),'Amber':(1,.43,.1,1),'Dark':(.012,.018,.022,1)}
mats={}
for n,c in colors.items():
 m=bpy.data.materials.new('AWC_'+n);m.diffuse_color=c;m.use_nodes=True
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.78;bs.inputs['Metallic'].default_value=.7 if n in ['Steel','Rust'] else 0
 mats[n]=m
parts=[];records=[]
def finish(o,name,mat):
 o.name=name;o.data.materials.append(mats[mat]);parts.append(o);return o
def box(n,p,s,mat='Steel',bevel=1.2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  m=o.modifiers.new('Rounded manufactured edges','BEVEL');m.width=bevel;m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name)
 return finish(o,n,mat)
def cylinder(n,p,r,depth,mat='Steel',direction=(0,0,1),verts=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=p);o=bpy.context.object;o.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler();return finish(o,n,mat)
def beam(n,a,b,r=3,mat='Steel'):
 a=Vector(a);b=Vector(b);return cylinder(n,(a+b)/2,r,(b-a).length,mat,b-a,12)
def export(name):
 global parts
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # Author source counterpart of UE +Y. All kit placements use normal +1 actor scales.
 for v in o.data.vertices:v.co.y=-v.co.y
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Surface150cm')
 for p in o.data.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
  for li in p.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/150,v[axes[1]]/150)
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_space_transform=False,axis_forward='X',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False)
 records.append({'name':name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'materials':[m.name for m in o.data.materials]});parts=[]
 return o

# Five-metre two-storey facade: closed doors, inset warm windows, balcony and braces.
box('Masonry',(0,18,340),(500,60,680),'Stone',3)
for x in [-246,0,246]:box('Upright',(x,-20,340),(12,24,680),'Steel')
for z in [12,325,650]:box('Crossrail',(0,-29,z),(505,22,16),'Rust')
box('Door recess',(0,-20,125),(132,28,245),'Dark')
box('Door leaf',(0,-42,121),(108,8,225),'Steel')
for x in [-62,62]:box('Door jamb',(x,-48,124),(10,16,248),'Rust')
box('Door head',(0,-48,249),(134,16,12),'Rust');cylinder('Door handle',(35,-53,122),4,16,'Rust',(1,0,0))
for x,z in [(-157,165),(155,165),(-157,455),(70,455)]:
 box('Window black',(x,-20,z),(88,25,134),'Dark');box('Window glass',(x,-37,z),(66,2,107),'Amber',0)
 for dx in [-44,0,44]:box('Window bars',(x+dx,-46,z),(5,10,138),'Steel',.5)
 for dz in [-66,0,66]:box('Window sill',(x,-48,z+dz),(93,16,5),'Rust',.5)
box('Balcony',(0,-95,335),(505,140,12),'Steel')
for x in range(-245,246,70):beam('Balcony post',(x,-155,340),(x,-155,430),3)
for z in [385,435]:beam('Balcony rail',(-250,-155,z),(250,-155,z),3)
for x in [-220,220]:beam('Balcony brace',(x,-15,220),(x,-135,328),5,'Rust')
export('SM_C1_WorkerFacade')

# Patched sloping canopy; front drops under its own weight.
verts=[];faces=[]
for j in range(7):
 for i in range(13):
  x=-250+i*500/12;y=-j*260/6;z=310-j*40/6-16*math.sin(math.pi*i/12)*math.sin(math.pi*j/6);verts.append((x,y,z))
for j in range(6):
 for i in range(12):
  a=j*13+i;faces.append((a,a+1,a+14,a+13))
mesh=bpy.data.meshes.new('TensionedCloth');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new('Awning',mesh);scene.collection.objects.link(o);finish(o,'Awning','Cloth')
sol=o.modifiers.new('Fabric edge','SOLIDIFY');sol.thickness=1.5;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)
for x in [-235,235]:beam('Awning pole',(x,-250,0),(x,-250,290),3);beam('Awning tie',(x,0,312),(x,-260,275),2,'Rust')
export('SM_C1_ClothAwning')

# Water ration station with receiving basin, pipes and a wheel.
box('Base',(0,0,12),(210,125,24),'Stone');box('Pump body',(-50,12,94),(88,80,165),'Steel',4)
cylinder('Pressure vessel',(44,20,150),37,230,'Rust')
for z in [48,175,245]:cylinder('Vessel band',(44,20,z),40,9,'Steel')
beam('Feed pipe',(-88,0,160),(-88,0,260),9,'Rust');beam('Outlet',(-88,0,260),(-88,-75,260),9,'Rust')
box('Basin',(-66,-70,90),(108,85,12),'Steel')
for x in [-119,-13]:box('Basin edge',(x,-70,102),(7,85,25),'Rust')
box('Basin back',(-66,-112,102),(110,7,25),'Rust')
bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,location=(-48,-44,175),major_radius=22,minor_radius=3,rotation=(math.pi/2,0,0));finish(bpy.context.object,'Pump wheel','Rust')
for ang in [0,math.pi/2]:beam('Wheel spoke',(-48-22*math.cos(ang),-44,175-22*math.sin(ang)),(-48+22*math.cos(ang),-44,175+22*math.sin(ang)),2)
export('SM_C1_WaterPump')

cylinder('Can body',(0,0,27),19,50,'Rust');cylinder('Can rim',(0,0,53),21,5,'Steel');cylinder('Can lid',(0,0,56),19,2,'Steel')
beam('Handle L',(-14,0,54),(-14,0,72),1.5);beam('Handle top',(-14,0,72),(14,0,72),1.5);beam('Handle R',(14,0,72),(14,0,54),1.5)
export('SM_C1_WaterCan')

# Arch across Y, module advances along X.
for y in [-320,320]:
 box('Arch foot',(0,y,15),(85,65,30),'Stone');box('Arch leg',(0,y,205),(22,25,400),'Rust')
 for z in [75,175,275,375]:box('Bolt plate',(-14,y,z),(7,42,48),'Steel')
last=None
for i in range(17):
 a=math.pi*i/16;p=(0,320*math.cos(a),400+150*math.sin(a))
 if last:beam('Segmented arch',last,p,13,'Rust')
 last=p
for y in [-280,280]:beam('Arch knee',(0,y,300),(0,y*.7,460),5)
export('SM_C1_TunnelFrame')

box('Deck plate',(0,0,-7),(400,280,14),'Steel')
for x in [-193,193]:box('Deck end',(x,0,-22),(14,290,40),'Rust')
for y in [-136,136]:box('Deck girder',(0,y,-30),(400,14,65),'Rust')
for x in range(-175,176,50):box('Tread seam',(x,0,.6),(2,268,1.2),'Rust',.2)
export('SM_C1_CatwalkDeck')

for x in [-200,0,200]:box('Rail post',(x,0,55),(7,8,110),'Steel')
for z in [8,58,112]:box('Rail length',(0,0,z),(405,7,7 if z>10 else 15),'Rust')
for x in [-195,195]:box('Foot plate',(x,0,3),(22,20,6),'Steel')
export('SM_C1_RailPanel')

box('Frame header',(0,0,410),(100,720,50),'Steel',3)
for y in [-355,355]:
 box('Gate column',(0,y,205),(80,60,410),'Rust',3)
 for z in [80,200,320]:box('Gate rivetplate',(-44,y,z),(12,90,55),'Steel')
export('SM_C1_DepartureFrame')

box('Gate slab',(0,0,195),(30,640,390),'Steel',3)
for y in [-300,0,300]:box('Gate stiffener',(-20,y,195),(15,15,390),'Rust')
for z in [20,195,370]:box('Gate crossbar',(-20,0,z),(15,640,15),'Rust')
export('SM_C1_DepartureGate')

cylinder('Lamp mounting',(0,0,0),20,8,'Steel');cylinder('Glass',(0,0,-24),14,40,'Amber')
for z in [-5,-44]:cylinder('Lamp cap',(0,0,z),21,7,'Steel')
for i in range(8):
 a=i*math.tau/8;beam('Lamp guard',(17*math.cos(a),17*math.sin(a),-6),(17*math.cos(a),17*math.sin(a),-44),1.1)
export('SM_C1_CagedLamp')

bpy.data.libraries.write(str(OUT/'Chapter01_Kit.blend'),{scene},fake_user=True)
report={'scene':scene.name,'units':'centimetres','original_geometry':True,'export':'FBX mesh only, no cameras/lights; +1 UE instance scale','meshes':records,'total_triangles':sum(r['triangles'] for r in records)}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));result=report
