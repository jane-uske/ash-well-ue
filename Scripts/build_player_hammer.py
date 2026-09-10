"""Original maintenance hammer. Two game meshes, no inspection camera/light export."""
import bpy,math,json,bmesh
from pathlib import Path
R=Path(__file__).resolve().parents[1];OUT=R/'SourceAssets/PlayerHammer';OUT.mkdir(exist_ok=True)
scene=bpy.data.scenes.new('AW_PlayerHammer_Polish');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
colors={'Steel':(.13,.16,.17,1),'Edge':(.35,.38,.38,1),'Rubber':(.018,.023,.024,1),'Ochre':(.42,.23,.065,1)}
mats={}
for n,c in colors.items():
 m=bpy.data.materials.new('AW_Hammer_'+n);m.diffuse_color=c;m.use_nodes=True
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=c;bs.inputs['Metallic'].default_value=0 if n=='Rubber' else .8;bs.inputs['Roughness'].default_value=.85 if n=='Rubber' else .58;mats[n]=m
pieces=[]
def box(n,pos,size,mat,bevel=.3,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=n;o.dimensions=size;o.rotation_euler=rot
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mats[mat]);m=o.modifiers.new('Machined edge','BEVEL');m.width=bevel;m.segments=3
 bpy.ops.object.modifier_apply(modifier=m.name)
 for p in o.data.polygons:p.use_smooth=True
 m=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=m.name)
 pieces.append(o);return o
def join_export(name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in pieces:o.select_set(True)
 bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # FBX into UE reflects Y: author the source counterpart of hand-local +Y.
 for v in o.data.vertices:v.co.y=-v.co.y
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},use_space_transform=False,axis_forward='X',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',bake_anim=False)
 return {'name':name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'material_slots':[m.name for m in o.data.materials]}
# Local +Y follows the existing left-hand grip; runtime dimensions remain unchanged.
box('Forged shaft',(0,25,0),(3.3,62,3.0),'Steel',.6)
box('Grip core',(0,8,0),(4.1,24,3.6),'Rubber',.7)
for i in range(10):box('Grip rib',(0,-2+i*2.25,0),(4.3,.8,3.85),'Rubber',.25)
box('Heel ring',(0,-5.5,0),(4.8,2,4.2),'Edge',.4)
box('Impact collar',(0,46,0),(6.5,6,5.6),'Edge',.6)
handle=join_export('SM_PlayerHammer_Handle');pieces=[]
box('Forged head',(0,0,0),(25,14.5,16.5),'Steel',1.2)
for sign in [-1,1]:
 box('Striking face',(sign*12.4,0,0),(2.2,15.8,17.8),'Edge',.45)
 box('Side wear plate',(0,0,sign*8.1),(17,10,.6),'Ochre',.35)
 for x in [-6,6]:box('Retainer bolt',(x,0,sign*8.5),(1.3,1.3,.8),'Edge',.15)
box('Shaft socket',(0,-7.1,0),(7.2,3.5,7),'Steel',.7)
head=join_export('SM_PlayerHammer_Head')
bpy.data.libraries.write(str(OUT/'PlayerHammer.blend'),{scene},fake_user=True)
report={'origin':'Original Blender geometry, no external asset','units':'centimetres','handle_origin':'grip; Blender -Y becomes UE hand-local +Y','head_origin':'head centre; attached at grip +Y54cm','parts':[handle,head]}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));result=report
