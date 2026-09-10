from pathlib import Path
import bpy,math,json
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/BattlePolish';O.mkdir(parents=True,exist_ok=True)
scene=bpy.data.scenes.new('AW_BattlePolish_Kit');bpy.context.window.scene=scene
col=scene.collection
# Lightweight ring used for brief ground impact accents.
verts=[];faces=[]
for i in range(64):
 a=i*math.tau/64
 for r in [.47,.50]:verts.append((r*math.cos(a),r*math.sin(a),0))
for i in range(64):j=(i+1)%64;faces.append((2*i,2*j,2*j+1,2*i+1))
m=bpy.data.meshes.new('BattleShockRing');m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new('SM_BattleShockRing',m);col.objects.link(o)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(O/'SM_BattleShockRing.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
# Four broad curved iron ribs form one overhead vault; geometry is metres in source.
parts=[]
for y in [-4,-1.3,1.3,4]:
 for i in range(14):
  a=(i+.5)*math.pi/14
  bpy.ops.mesh.primitive_cube_add(size=1,location=(7*math.cos(a),y,7*math.sin(a)))
  b=bpy.context.object;b.name='VaultRib';b.scale=(.38,.30,math.pi*7/14+.12);b.rotation_euler[1]=-a;parts.append(b)
for x in [-7,7]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,-3));b=bpy.context.object;b.scale=(.45,8.5,.45);parts.append(b)
bpy.ops.object.select_all(action='DESELECT')
for b in parts:b.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name='SM_BattleVault'
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.export_scene.fbx(filepath=str(O/'SM_BattleVault.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
bpy.data.libraries.write(str(O/'BattlePolishGeometry.blend'),{scene},compress=True)
result={'exports':['SM_BattleShockRing.fbx','SM_BattleVault.fbx'],'vault_dimensions_m':list(o.dimensions)}
