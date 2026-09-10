"""Derive a seated Warden mesh, trimming only the Body-weighted long skirt.
Original Warden rig, materials, UVs, limbs and source file remain unchanged.
Run in a disposable background Blender process.
"""
import bpy,bmesh,json,hashlib
from pathlib import Path

R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedBoss'
SOURCE=R/'SourceAssets/WardenRig/WardenRig.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01
rig=bpy.data.objects['WardenRig'];mesh=bpy.data.objects['SK_WardenRig']
original_vertices=len(mesh.data.vertices);original_faces=len(mesh.data.polygons)
body_group=mesh.vertex_groups.find('Body');assert body_group>=0
cut_height=100.0 # 2.3 cm below the original pelvis; below the mounted seat cushion.
body=mesh.copy();body.data=mesh.data.copy();body.name='MountedBodyTrimWork';s.collection.objects.link(body)

def isolate(obj,keep_body):
    bm=bmesh.new();bm.from_mesh(obj.data);weights=bm.verts.layers.deform.active
    is_body=lambda f: all(v[weights].get(body_group,0)>.999 for v in f.verts)
    delete=[f for f in bm.faces if is_body(f)!=keep_body]
    bmesh.ops.delete(bm,geom=delete,context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(obj.data);bm.free()

isolate(mesh,False);isolate(body,True)
preserved_limb_vertices=len(mesh.data.vertices)
bm=bmesh.new();bm.from_mesh(body.data)
before_body=len(bm.verts)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
    dist=.0001,plane_co=(0,0,cut_height),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
cut_edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-cut_height)<.002 for v in e.verts)]
caps=bmesh.ops.holes_fill(bm,edges=cut_edges,sides=0).get('faces',[]) if cut_edges else []
for f in caps:f.material_index=1;f.smooth=False
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
after_body=len(bm.verts);bm.to_mesh(body.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);body.select_set(True)
bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
mesh.name='SK_MountedRider';mesh.data.name='MountedRiderTrimmedGeometry'
rig.animation_data_clear()
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(O/'SK_MountedRider.fbx'),use_selection=True,
    object_types={'MESH','ARMATURE'},use_space_transform=False,axis_forward='X',axis_up='Z',
    add_leaf_bones=False,bake_anim=False,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE')
for ob in list(s.objects):
    if ob not in (mesh,rig):bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'MountedRiderPrepared.blend'))
report={
    'source':str(SOURCE.relative_to(R)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'change':'Only faces whose every vertex is fully Body weighted are trimmed below z=100 cm; new cut caps use the existing dark inner material.',
    'cut_height_cm':cut_height,'original_vertices':original_vertices,'original_faces':original_faces,
    'preserved_limb_vertices':preserved_limb_vertices,'body_vertices_before':before_body,'body_vertices_after':after_body,
    'output_vertices':len(mesh.data.vertices),'output_faces':len(mesh.data.polygons),'cut_cap_faces':len(caps),
    'bones':list(rig.data.bones.keys()),
    'required_driven_parts':['Body','RightUpperArm','RightForearm','LeftUpperArm','LeftForearm','RightThigh','RightShin','RightFoot','LeftThigh','LeftShin','LeftFoot'],
    'coordinate_contract':'Unchanged WardenRig RH centimetres; same 11 driven part bones plus original root/Hammer; UE native RH-to-LH conversion.',
    'materials':'Reuse /Game/AshWell/Combat/WardenHQ/M_WardenHQ and M_WardenHQ_Inner',
    'status':'Derived trim for mounted pose; runtime verification pending; not a new character model'
}
(O/'mounted_rider_manifest.json').write_text(json.dumps(report,indent=2))
print('MOUNTED_RIDER_READY',json.dumps(report))
