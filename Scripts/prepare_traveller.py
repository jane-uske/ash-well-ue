"""Adapt the generated body and Meshy weights to the project's existing skeleton.
The source rig, mesh and textures remain intact. Cloak and sword are independent assets.
Run in Blender MCP after loading TravellerSourceRig and SK_Intro_Protagonist_Rig.
"""
from pathlib import Path
import bpy,json,math,bmesh
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/SwordPass'
s=bpy.data.scenes.new('AW_Traveller_Game');bpy.context.window.scene=s
old=bpy.data.objects['SK_Intro_Protagonist_Rig'];source=bpy.data.objects['TravellerSourceRig'];sm=next(o for o in source.children if o.type=='MESH')
rig=old.copy();rig.data=old.data.copy();s.collection.objects.link(rig);rig.name='AW_Traveller_GameRig';rig.animation_data_clear()
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
mesh=sm.copy();mesh.data=sm.data.copy();mesh.parent=None;mesh.matrix_world=Matrix.Identity(4);s.collection.objects.link(mesh);mesh.name='SK_Traveller'
for m in list(mesh.modifiers):mesh.modifiers.remove(m)
C=Matrix(((0,-1,0),(1,0,0),(0,0,1)))
mp={'Hips':'pelvis','Spine02':'spine_01','Spine01':'spine_01','Spine':'spine_02','neck':'neck','Head':'head','head_end':'head','headfront':'head'}
child={'Hips':'Spine02','Spine02':'Spine01','Spine01':'Spine','Spine':'neck','neck':'Head','Head':'head_end'}
for ss,ts in [('Right','L'),('Left','R')]:
 for sb,tb in [('Arm','upperarm'),('ForeArm','forearm'),('Hand','hand'),('UpLeg','thigh'),('Leg','calf'),('Foot','foot'),('ToeBase','foot')]:mp[ss+sb]=tb+'_'+ts
 mp[ss+'Shoulder']='upperarm_'+ts
 for a,b in [('Arm','ForeArm'),('ForeArm','Hand'),('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase')]:child[ss+a]=ss+b
# Use actual joint heads: imported GLB bone display lengths are inflated and must not govern geometry.
heads={b.name:source.matrix_world@b.head_local for b in source.data.bones}
xf={}
for name,target in mp.items():
 ref=name
 if name.endswith('Shoulder'):ref=name.replace('Shoulder','Arm')
 if name.endswith('ToeBase'):ref=name.replace('ToeBase','Foot')
 if name in ['head_end','headfront']:ref='Head'
 if name=='Spine01':ref='Spine02'
 b=rig.data.bones[target];sh=heads[ref]
 if ref in child:sd=(heads[child[ref]]-sh).normalized()
 elif ref.endswith('Hand'):sd=(source.matrix_world.to_3x3()@(source.data.bones[ref].tail_local-source.data.bones[ref].head_local)).normalized()
 else:sd=Vector((0,0,1))
 td=(b.tail_local-b.head_local).normalized();q=(C@sd).rotation_difference(td)
 xf[name]=Matrix.Translation(b.head_local)@q.to_matrix().to_4x4()@C.to_4x4()@Matrix.Translation(-sh)
# Preserve source surface detail and UVs, using the actual auto-rig skin weights.
source_groups={g.index:g.name for g in sm.vertex_groups};weights=[]
for v in mesh.data.vertices:
 p=sm.matrix_world@v.co;ps=Vector();wts={};total=0
 for g in v.groups:
  n=source_groups[g.group]
  if n in xf:
   ps+=(xf[n]@p)*g.weight;total+=g.weight;tn=mp[n];wts[tn]=wts.get(tn,0)+g.weight
 if total>0:v.co=ps/total
 else:v.co=C@p
 weights.append(wts)
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
for n in set(mp.values()):mesh.vertex_groups.new(name=n)
for i,ws in enumerate(weights):
 total=sum(ws.values())
 if total:
  for n,w in ws.items():mesh.vertex_groups[n].add([i],w/total,'REPLACE')
# A static glove grasp on the weapon hand; no claim of a full finger animation rig.
hb=rig.data.bones['hand_L'].matrix_local;inv=hb.inverted();gi=mesh.vertex_groups['hand_L'].index
for v in mesh.data.vertices:
 weight=max([g.weight for g in v.groups if g.group==gi] or [0]);q=inv@v.co
 if weight>.25 and q.y>.055:
  theta=min(2.65,(q.y-.055)/.039);bent=q.copy();bent.y=.055+.027*math.sin(theta);bent.x+=.027*(1-math.cos(theta));v.co=v.co.lerp(hb@bent,min(1,weight*1.3))
for poly in mesh.data.polygons:poly.use_smooth=True
mesh.data.normals_split_custom_set([(0,0,0)]*len(mesh.data.loops))
mesh.parent=rig;mod=mesh.modifiers.new('Traveller skin','ARMATURE');mod.object=rig
# Body texture files are extracted once for deterministic UE PBR material creation.
images=[]
pbr=bpy.data.objects['Mesh_0'].data.materials[0]
mesh.data.materials.clear();mesh.data.materials.append(pbr)
for node in pbr.node_tree.nodes:
 if node.type=='TEX_IMAGE' and node.image:
  links=list(node.outputs['Color'].links)
  kind='Normal' if any(l.to_node.type=='NORMAL_MAP' for l in links) else 'MR' if any(l.to_node.type=='SEPARATE_COLOR' for l in links) else 'BaseColor'
  im=node.image
  if im in images:continue
  images.append(im);im.filepath_raw=str(O/('T_Traveller_'+kind+'.png'));im.file_format='PNG';im.save()
# Split rear cape: 2 panels with a real centre gap, shoulders follow spine, hem follows coat bones.
cloth=bpy.data.materials.new('M_TravellerCloak');cloth.use_nodes=True;bs=next(n for n in cloth.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.045,.052,.055,1);bs.inputs['Roughness'].default_value=.96
vs=[];faces=[];vweights=[]
for sign in [-1,1]:
 start=len(vs);rows=20;cols=16
 for j in range(rows+1):
  t=j/rows;z=1.47-.93*t;w=.245+.10*t
  for i in range(cols+1):
   a=i/cols;y=sign*(.006+.028*t+(w-.028*t)*a);x=-.16-.115*t-.009*math.cos(a*math.pi*7+t*2)*(t+.3)
   if j==rows:z+=.007*math.sin(a*37)+.006*math.cos(a*23)
   vs.append((x,y,z));vweights.append((t,'coat_L' if sign<0 else 'coat_R'))
 for j in range(rows):
  for i in range(cols):
   k=start+j*(cols+1)+i;f=(k,k+1,k+cols+2,k+cols+1);faces.append(f if sign>0 else tuple(reversed(f)))
me=bpy.data.meshes.new('TravellerSplitCloak');me.from_pydata(vs,[],faces);me.update();cape=bpy.data.objects.new('SK_TravellerCloak',me);s.collection.objects.link(cape);me.materials.append(cloth)
for n in ['spine_02','pelvis','coat_L','coat_R']:cape.vertex_groups.new(name=n)
for i,(t,side) in enumerate(vweights):
 top=max(0,1-t*2);hem=max(0,(t-.45)/.55)*.75
 for n,w in [('spine_02',top),('pelvis',1-top-hem),(side,hem)]:
  if w>0:cape.vertex_groups[n].add([i],w,'REPLACE')
for p in me.polygons:p.use_smooth=True
cape.parent=rig;mod=cape.modifiers.new('Cloak skin','ARMATURE');mod.object=rig
# A folded fabric collar gives the shoulder/neck silhouette without obscuring the face.
cv=[];cf=[]
for j in range(5):
 t=j/4
 for i in range(49):
  a=i/48*math.tau;rad=.105+.135*t
  cv.append((.02+rad*math.cos(a),rad*1.2*math.sin(a),1.455-.12*t*(.55+.45*math.cos(a))+.008*math.cos(a*6)*t))
for j in range(4):
 for i in range(48):
  k=j*49+i;cf.append((k,k+1,k+50,k+49))
cm=bpy.data.meshes.new('DrapedNeckMantle');cm.from_pydata(cv,[],cf);cm.update();collar=bpy.data.objects.new('TravellerFoldedCollar',cm);s.collection.objects.link(collar);cm.materials.append(cloth)
for poly in cm.polygons:poly.use_smooth=True
g=collar.vertex_groups.new(name='spine_02');g.add(list(range(len(collar.data.vertices))),1,'REPLACE');collar.parent=rig;m=collar.modifiers.new('Collar skin','ARMATURE');m.object=rig
bpy.ops.object.select_all(action='DESELECT');cape.select_set(True);collar.select_set(True);bpy.context.view_layer.objects.active=cape;bpy.ops.object.join()
cape.data.materials.clear();cape.data.materials.append(cloth)
for poly in cape.data.polygons:poly.material_index=0
# UVs only on original cloak; generated body's UVs remain untouched.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
for ob,name in [(mesh,'SK_Traveller'),(cape,'SK_TravellerCloak')]:
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=rig
 occupied=bpy.data.objects.get('SK_Intro_Protagonist_Rig');original=rig.name
 if occupied and occupied!=rig:occupied.name='AW_PreservedPlayerRig'
 rig.name='SK_Intro_Protagonist_Rig'
 bpy.ops.export_scene.fbx(filepath=str(O/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',primary_bone_axis='Y',secondary_bone_axis='X')
 rig.name=original
 if occupied and occupied!=rig:occupied.name='SK_Intro_Protagonist_Rig'
bpy.data.libraries.write(str(O/'TravellerPrepared.blend'),{s},compress=True,fake_user=True)
report={'source':'Meshy image-to-3d + auto-rig, derived from approved original traveller reference','skeleton':'/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton','body_triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'cloak_triangles':sum(len(p.vertices)-2 for p in cape.data.polygons),'images':[im.filepath_raw for im in images],'limitations':['Cloth is separately skinned, not simulated','Hand skin has no independent finger animation','Reusing existing skeleton proportions; extreme poses require visual review']}
(O/'hero-manifest.json').write_text(json.dumps(report,indent=2));result=report
