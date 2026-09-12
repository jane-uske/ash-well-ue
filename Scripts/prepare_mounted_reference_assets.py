"""Blender: inspect and prepare independent Meshy derivatives and a continuous field."""
import bpy
import bmesh
import hashlib
import json
import math
import os
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'SourceAssets/MountedReferenceProduction'
OUT.mkdir(parents=True, exist_ok=True)
ledger = json.loads((ROOT/'Docs/Implementation/MountedBoss/ChargeSample/meshy-reference-budget.json').read_text())
report = {'assets': {}, 'scope': 'Offline geometry and export checks; UE acceptance remains pending.'}
only = os.environ.get('ASHWELL_REFERENCE_PROP')
if only and (OUT/'preparation.json').exists():
    report=json.loads((OUT/'preparation.json').read_text())


def export(obj, name):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=.01
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')), use_selection=True,
        object_types={'MESH'}, axis_forward='X', axis_up='Z', use_space_transform=False,
        add_leaf_bones=False, bake_anim=False, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE')


for key, label in [('wall','RuinWall'),('rock','FlatRock'),('stake','RoadsideStake'),('castle','DistantFortress')]:
    if key not in ledger['assets'] or (only and only!=key):continue
    entry=ledger['assets'][key]; assert entry['status']=='downloaded'
    source=ROOT/entry['project_dir']/'model.glb'
    original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']; assert meshes
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        transform=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=transform;obj.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.join();obj=bpy.context.object;obj.name='SM_Reference'+label
    points=[v.co.copy() for v in obj.data.vertices]
    low=Vector([min(v[i] for v in points) for i in range(3)])
    high=Vector([max(v[i] for v in points) for i in range(3)])
    before=list(high-low)
    if key!='stake' and high.y-low.y>high.x-low.x:
        obj.data.transform(Matrix.Rotation(math.pi/2,4,'Z'))
        points=[v.co.copy() for v in obj.data.vertices]
        low=Vector([min(v[i] for v in points) for i in range(3)])
        high=Vector([max(v[i] for v in points) for i in range(3)])
    scale=400/(high.z-low.z) if key=='stake' else {'wall':400,'rock':330,'castle':9000}[key]/(high.x-low.x)
    anchor=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    obj.data.transform(Matrix.Scale(scale,4)@Matrix.Translation(-anchor))
    mesh=bmesh.new();mesh.from_mesh(obj.data)
    split_boundary_edges=sum(not e.is_manifold for e in mesh.edges)
    # GLB duplicates vertices at UV/normal seams. Weld positions while retaining
    # per-corner UVs before measuring actual open or nonmanifold geometry.
    bmesh.ops.remove_doubles(mesh,verts=list(mesh.verts),dist=.001)
    bmesh.ops.recalc_face_normals(mesh,faces=list(mesh.faces))
    nonmanifold=sum(not e.is_manifold for e in mesh.edges)
    mesh.to_mesh(obj.data);obj.data.update()
    mesh.free()
    assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co)
    bpy.context.view_layer.update()
    sizes=list(obj.dimensions)
    triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
    assert 100<triangles<50000,(key,triangles)
    export(obj,obj.name)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(label+'.blend')))
    report['assets'][key]={'task_id':entry['task_id'],'source':str(source.relative_to(ROOT)),
        'original_sha256':original_hash,'raw_dimensions_m':before,'dimensions_cm':sizes,
        'triangles':triangles,'split_boundary_edges_before_weld':split_boundary_edges,
        'nonmanifold_edges':nonmanifold,'materials':len(obj.data.materials),
        'fbx':obj.name+'.fbx','uniform_scale':scale,'uv_layers':len(obj.data.uv_layers),
        'backside':'inferred by generation; not visible in source reference'}
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash
    print('REFERENCE_PREPARED',key,report['assets'][key],flush=True)

if only:
    (OUT/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0)

import runpy
height=runpy.run_path(str(ROOT/'Scripts/mounted_reference_layout.py'))['ground']

bpy.ops.wm.read_factory_settings(use_empty=True)
xs=sorted(set(list(range(-18000,-3000,200))+list(range(-3000,3001,50))+list(range(3200,18001,200))))
ys=sorted(set(list(range(-14000,-2400,200))+list(range(-2400,2401,50))+list(range(2600,14001,200))))
# FBX +X-forward to UE converts Blender XY to UE (-Y,-X).
# Author elevations in final UE coordinates so instances and physical ground agree.
verts=[(x,y,height(-y,-x)) for y in ys for x in xs]
faces=[];width=len(xs)
for j in range(len(ys)-1):
    for i in range(width-1):
        a=j*width+i;faces.append((a,a+1,a+1+width,a+width))
mesh=bpy.data.meshes.new('ContinuousReferenceField');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('SM_ReferenceField',mesh);bpy.context.collection.objects.link(obj)
uv=mesh.uv_layers.new(name='GroundUV')
for polygon in mesh.polygons:
    polygon.use_smooth=True
    for index in polygon.loop_indices:
        p=mesh.vertices[mesh.loops[index].vertex_index].co
        uv.data[index].uv=(p.x/400,p.y/400)
export(obj,obj.name)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ReferenceField.blend'))
report['terrain']={'vertices':len(verts),'triangles':len(faces)*2,'bounds_cm':[-18000,18000,-14000,14000],
                   'near_grid_spacing_cm':50,'home_height_cm':height(0,0),
                   'samples_cm':[{ 'xy':[x,y],'z':height(x,y)} for x,y in [(0,0),(-2050,0),(850,0),(0,-1400),(0,1400)]]}
(OUT/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('REFERENCE_PREPARATION_COMPLETE',flush=True)
