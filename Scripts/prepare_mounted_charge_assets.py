"""Prepare isolated textured Meshy derivatives; originals remain immutable.
Run with background Blender. Retains texture UVs and transfers existing skin.
"""
import bpy, json, math, struct, hashlib
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

R=Path(__file__).resolve().parents[1]
O=R/'SourceAssets/MountedChargeSample';O.mkdir(exist_ok=True,parents=True)
REPORT={}

def import_glb(p):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(p))
    added=set(bpy.data.objects)-before
    rigs=[o for o in added if o.type=='ARMATURE']
    shapes={b.custom_shape for rig in rigs for b in rig.pose.bones if b.custom_shape}
    return [o for o in added if o.type=='MESH' and o not in shapes],rigs

def bounds(ob):
    ps=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    return Vector([min(p[i] for p in ps) for i in range(3)]),Vector([max(p[i] for p in ps) for i in range(3)])

def active(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob

def extract(p,label):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=28+n
    for i,name in enumerate(['BaseColor','MR','Normal']):
        im=g['images'][g['textures'][i]['source']];v=g['bufferViews'][im['bufferView']]
        ext='jpg' if im['mimeType']=='image/jpeg' else 'png'
        (O/f'T_{label}_{name}.{ext}').write_bytes(b[off+v.get('byteOffset',0):off+v.get('byteOffset',0)+v['byteLength']])

def export(mesh,rig,label):
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True)
    if rig:rig.select_set(True)
    bpy.context.view_layer.objects.active=rig or mesh
    bpy.ops.export_scene.fbx(filepath=str(O/f'{label}.fbx'),use_selection=True,
        object_types={'MESH','ARMATURE'} if rig else {'MESH'},use_space_transform=False,
        axis_forward='X',axis_up='Z',add_leaf_bones=False,bake_anim=False,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',mesh_smooth_type='FACE')

for label,folder,target,rotation in [
    ('Knight','20260911_201322_gilded-sentinel_01a08e8e',90000,math.pi/2),
    ('Horse','20260911_201320_gilded-warhorse_01a08f11',140000,math.pi),
]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=O/'originals'/f'{label.lower()}_textured.glb'
    skinned=R/'meshy_output'/folder/'rigged.glb'
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,skinned]}
    oldmeshes,rigs=import_glb(skinned);old=oldmeshes[0];rig=rigs[0]
    old.name='WeightSource';rig.name=f'Sample{label}Rig'
    highmeshes,_=import_glb(source);mesh=highmeshes[0];mesh.name=f'SK_Sample{label}'
    lo,hi=bounds(old);slo,shi=bounds(mesh)
    scale=(hi.z-lo.z)/(shi.z-slo.z)
    shift=(lo+hi)/2-(slo+shi)/2*scale
    mesh.matrix_world=Matrix.Translation(shift)@Matrix.Scale(scale,4)@mesh.matrix_world
    active(mesh);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    triangles=sum(len(p.vertices)-2 for p in mesh.data.polygons)
    dec=mesh.modifiers.new('Derived game mesh','DECIMATE');dec.ratio=min(1,target/triangles)
    dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
    transfer=mesh.modifiers.new('Existing Meshy skin','DATA_TRANSFER');transfer.object=old
    transfer.use_vert_data=True;transfer.data_types_verts={'VGROUP_WEIGHTS'};transfer.vert_mapping='POLYINTERP_NEAREST'
    bpy.ops.object.datalayout_transfer(modifier=transfer.name)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    unweighted=sum(not any(g.weight>1e-6 for g in v.groups) for v in mesh.data.vertices)
    if unweighted:raise RuntimeError(f'{label}: {unweighted} unweighted vertices')
    # Geometry fit is measured against the existing skin before normalizing axes.
    kd=KDTree(len(old.data.vertices))
    for v in old.data.vertices:kd.insert(old.matrix_world@v.co,v.index)
    kd.balance();stride=max(1,len(mesh.data.vertices)//2000)
    distances=[kd.find(v.co)[2]*100 for i,v in enumerate(mesh.data.vertices) if i%stride==0]
    distances.sort()
    mesh.parent=rig;mesh.matrix_parent_inverse=rig.matrix_world.inverted()
    arm=mesh.modifiers.new('Sample skin','ARMATURE');arm.object=rig
    # Bake the coordinate conversion into both the rest skeleton and mesh data.
    rotation_matrix=Matrix.Rotation(rotation,4,'Z')
    mesh.parent=None;mesh.matrix_world=rotation_matrix@mesh.matrix_world
    rig.matrix_world=rotation_matrix@rig.matrix_world
    for ob in [mesh,rig]:
        active(ob);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        ob.data.transform(Matrix.Scale(100,4))
    mesh.parent=rig;mesh.matrix_parent_inverse=Matrix.Identity(4)
    for b in rig.pose.bones:b.custom_shape=None
    for ob in list(bpy.data.objects):
        if ob not in [mesh,rig]:bpy.data.objects.remove(ob,do_unlink=True)
    s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01;s.render.fps=60
    extract(source,label)
    export(mesh,rig,mesh.name)
    bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{label}Prepared.blend'))
    REPORT[label]={'source_hashes':hashes,'triangles_before':triangles,'triangles_after':sum(len(p.vertices)-2 for p in mesh.data.polygons),
        'unweighted_vertices':unweighted,'fit_scale':scale,'fit_shift_m':list(shift),'surface_distance_cm_p50':distances[len(distances)//2],
        'surface_distance_cm_p95':distances[int(len(distances)*.95)],'bones':{b.name:{'head_cm':list(b.head_local),'tail_cm':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}}
    for p,h in hashes.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    (O/'prepared_manifest.json').write_text(json.dumps(REPORT,indent=2));print('PREPARED',label,REPORT[label]['triangles_after'],flush=True)

for label,folder,desired_height in [('Poleaxe','20260911_201214_tree-sentinel-halberd_87d0ac80',245),('Shield','20260911_201130_tree-sentinel-shield_cad64068',105)]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=R/'meshy_output'/folder/'model.glb';meshes,_=import_glb(source);mesh=meshes[0]
    mesh.name=f'SM_Sample{label}';lo,hi=bounds(mesh)
    scale=desired_height/(hi.z-lo.z)
    center=(lo+hi)/2
    # Poleaxe is authored along +X with grip 30% above its bottom; shield stays upright.
    anchor=Vector((center.x,center.y,lo.z+(hi.z-lo.z)*.30)) if label=='Poleaxe' else center
    rot=Matrix.Rotation(math.pi/2,4,'Y') if label=='Poleaxe' else Matrix.Identity(4)
    mesh.matrix_world=rot@Matrix.Scale(scale,4)@Matrix.Translation(-anchor)@mesh.matrix_world
    active(mesh);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    tris=sum(len(p.vertices)-2 for p in mesh.data.polygons)
    dec=mesh.modifiers.new('Derived game mesh','DECIMATE');dec.ratio=24000/tris;dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
    extract(source,label);export(mesh,None,mesh.name)
    bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{label}Prepared.blend'))
    REPORT[label]={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'triangles_before':tris,'triangles_after':sum(len(p.vertices)-2 for p in mesh.data.polygons),'height_cm':desired_height}
    (O/'prepared_manifest.json').write_text(json.dumps(REPORT,indent=2));print('PREPARED',label,flush=True)
