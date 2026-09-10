"""Original plain arming sword; independent equipment, centimetre FBX."""
import bpy,math,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/SwordPass'
s=bpy.data.scenes.new('AW_TravellerSword');bpy.context.window.scene=s;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01
mats={}
for n,c,metal,rough in [('Blade',(.28,.32,.35,1),.95,.33),('Iron',(.07,.075,.08,1),.85,.55),('Grip',(.05,.032,.019,1),0,.9),('Trim',(.18,.15,.105,1),.8,.6)]:
 m=bpy.data.materials.new('M_Sword_'+n);m.diffuse_color=c;m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=c;bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;mats[n]=m
parts=[]
def box(n,loc,dims,mat,bevel=.2):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[mat]);mod=o.modifiers.new('Forged bevel','BEVEL');mod.width=bevel;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name);parts.append(o);return o
# Diamond section creates readable sharp cutting edges under actual lights.
vs=[];fs=[]
sections=[(13,2.9,.52),(19,2.8,.48),(70,2.25,.38),(88,1.65,.30),(101,.04,.025)]
for y,w,t in sections:vs += [(-w,y,0),(0,y,t),(w,y,0),(0,y,-t)]
for i in range(len(sections)-1):
 for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
fs.extend([(3,2,1,0),(16,17,18,19)])
me=bpy.data.meshes.new('ForgedBlade');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('ForgedBlade',me);s.collection.objects.link(ob);me.materials.append(mats['Blade']);parts.append(ob)
box('Leather grip',(0,0,0),(3.3,22,2.9),'Grip',.8)
for i in range(12):box('Wrapped leather seam',(0,-10+i*1.75,0),(3.45,.5,3.05),'Grip',.2)
box('Crossguard',(0,12,0),(23,2.7,3.3),'Iron',.8)
for sign in [-1,1]:box('Guard tip',(sign*11,10.8,0),(2.9,4.7,3.6),'Trim',.7)
box('Pommel',(0,-13.3,0),(5.1,5,3.8),'Iron',1.6)
box('Ferrule',(0,9,0),(3.6,1.8,3.3),'Trim',.3)
def export(name,objs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;s.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 for v in o.data.vertices:v.co.y=-v.co.y
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.export_scene.fbx(filepath=str(O/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_space_transform=False,axis_forward='X',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False)
 return o
sword=export('SM_TravellerSword',parts);parts=[]
box('Scabbard',(0,55,0),(6.4,87,2.7),'Grip',1.2)
box('Mouth',(0,12,0),(7,4,3.3),'Iron',.5);box('Chape',(0,97,0),(5,7,3),'Iron',1)
scabbard=export('SM_TravellerScabbard',parts)
bpy.data.libraries.write(str(O/'TravellerSword.blend'),{s},compress=True,fake_user=True)
(O/'sword-manifest.json').write_text(json.dumps({'source':'Original Blender mesh, no external asset','units':'centimetres','blade_cm':[14,101],'grip_origin_cm':[0,0,0],'runtime_axis':'+X','materials':list(mats),'triangles':sum(len(p.vertices)-2 for p in sword.data.polygons)},indent=2))
result={'sword':sword.name,'scabbard':scabbard.name}
