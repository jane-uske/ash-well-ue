"""Background Blender preparation of the approved Warden HQ, without redesign.

Run Blender --background --factory-startup --python Scripts/prepare_warden_hq.py.
Source GLB is immutable. Blender/FBX use normalized RH centimeter coordinates;
Unreal's mandatory RH-to-LH conversion reflects Y. The manifest records final
UE LH coordinates separately from the Blender inspection coordinates. Import with
convert_scene=False, convert_scene_unit=False, uniform scale 1. No lights/cameras
are exported. The inspection blend contains local inspection lights/camera only.
"""
import bpy, bmesh, json, math, shutil, hashlib
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/rare/dev/ash-well-local3d/results/warden-hq-v01')
OUT = ROOT / 'SourceAssets/WardenHQ'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
bpy.ops.import_scene.gltf(filepath=str(SOURCE/'warden_pbr.glb'))
src = [o for o in scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = src
src.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
input_tris = sum(len(p.vertices)-2 for p in src.data.polygons)
# glTF carries duplicate vertices at UV seams. Weld positions before collapse,
# retaining UVs on face corners, or independently collapsed seam edges crack.
bm=bmesh.new();bm.from_mesh(src.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
bm.to_mesh(src.data);bm.free();src.data.update()
# Original surface is already softly reconstructed. Retain 65% of triangles,
# preserving original corner UVs; don't remesh or regenerate appearance.
dec = src.modifiers.new('Conservative surface simplification', 'DECIMATE')
dec.ratio = .65
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dec.name)
reduced_tris = sum(len(p.vertices)-2 for p in src.data.polygons)
scene.unit_settings.scale_length = .01
feet_z = -.8940808176994324
center_x = .105
scale = 270 / (.989990234375 - feet_z)
def normalized_rh(p):
    x,y,z = p
    return Vector((-y*scale,(x-center_x)*scale,(z-feet_z)*scale))

def to_unreal_lh(p):
    return [p[0],-p[1],p[2]]

joint_source = {
    'RightShoulder':(-.235,.015,.54), 'RightElbow':(-.31,-.015,.285),
    'RightHand':(-.354,-.056,-.077), 'LeftShoulder':(.435,.015,.54),
    'LeftElbow':(.50,-.015,.285), 'LeftHand':(.533,-.056,-.077),
    'RightHip':(-.065,.025,-.18),'RightKnee':(-.105,.018,-.55),
    'RightAnkle':(-.115,-.005,-.81),'LeftHip':(.33,.025,-.18),
    'LeftKnee':(.34,.018,-.55),'LeftAnkle':(.34,-.005,-.81),
    'HammerGrip':(-.354,-.056,-.077), 'HammerHead':(-.494,-.03,-.797),
    'HammerTip':(-.535,-.045,-.998),
}
joints = {k:normalized_rh(v) for k,v in joint_source.items()}
def classify(c):
    x,y,z = c
    # Shaft below the fist is clear of the coat. The upper cut is hidden in
    # the gripping hand; unlike the input, the weapon now has its own pivot.
    if x < -.305 and z < -.155:
        return 'Hammer'
    if -.155 <= z < .495:
        if x < (-.15 if z > .22 else -.255):
            return 'RightUpperArm' if z >= .285 else 'RightForearm'
        if x > (.40 if z > .22 else .44):
            return 'LeftUpperArm' if z >= .285 else 'LeftForearm'
    # Leave the skirt with the body; only the visible trouser/boot interior
    # moves. The material stays uninterrupted in the assembled rest pose.
    leg = z < -.66 or (z < -.22 and -.14 < y < .135)
    if leg:
        side = 'Right' if x < .13 else 'Left'
        if z < -.805: return side+'Foot'
        if z < -.56: return side+'Shin'
        return side+'Thigh'
    return 'Body'

groups = {}
labels=[]
for p in src.data.polygons:
    c = sum((src.data.vertices[i].co for i in p.vertices), Vector())/len(p.vertices)
    label=classify(c);labels.append(label)
    groups.setdefault(label, []).append(p.index)
assert sum(map(len,groups.values())) == len(src.data.polygons)
# Spatial cuts may leave an inner cuff or knee flap behind in the torso group.
# Reassign those small islands to the neighbor they actually shared cut edges
# with, so raising a forearm doesn't leave floating fragments at its old place.
edge_faces={}
for p in src.data.polygons:
    for edge in p.edge_keys:edge_faces.setdefault(edge,[]).append(p.index)
adj=[set() for _ in labels]
for ids in edge_faces.values():
    for i in ids:adj[i].update(j for j in ids if j!=i)
reassigned=0
for name,ids in list(groups.items()):
    unseen=set(ids);components=[]
    while unseen:
        start=unseen.pop();stack=[start];component=[start]
        while stack:
            i=stack.pop();new=adj[i]&unseen
            unseen.difference_update(new);component.extend(new);stack.extend(new)
        components.append(component)
    components.sort(key=len,reverse=True)
    for component in components[1:]:
        neighbors={}
        for i in component:
            for j in adj[i]:
                if labels[j]!=name:neighbors[labels[j]]=neighbors.get(labels[j],0)+1
        if not neighbors:continue
        destination=max(neighbors,key=neighbors.get) if name=='Body' else ('Body' if 'Body' in neighbors else name)
        for i in component:labels[i]=destination
        reassigned+=len(component)
groups={}
for i,label in enumerate(labels):groups.setdefault(label,[]).append(i)
material = src.data.materials[0]
material.name = 'M_WardenHQ_Surface'
inner = bpy.data.materials.new('M_WardenHQ_Inner')
inner.diffuse_color=(.025,.022,.018,1)
inner.use_nodes=True
bs=inner.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.025,.022,.018,1)
bs.inputs['Roughness'].default_value=.85
uv_src = src.data.uv_layers.active.data
parts = {}
audit_parts = {}
for name, face_ids in groups.items():
    vert_map, verts, faces, uv_faces = {}, [], [], []
    for pi in face_ids:
        p=src.data.polygons[pi]
        outface=[]
        for vi in p.vertices:
            if vi not in vert_map:
                vert_map[vi]=len(verts);verts.append(normalized_rh(src.data.vertices[vi].co))
            outface.append(vert_map[vi])
        faces.append(outface)
        uv_faces.append([uv_src[li].uv.copy() for li in p.loop_indices])
    mesh=bpy.data.meshes.new('WardenHQ_'+name)
    mesh.from_pydata(verts,[],faces);mesh.update()
    mesh.materials.append(material);mesh.materials.append(inner)
    layer=mesh.uv_layers.new(name='UVMap')
    for p,uvs in zip(mesh.polygons,uv_faces):
        p.use_smooth=True
        for li,uv in zip(p.loop_indices,uvs):layer.data[li].uv=uv
    # Weld duplicate UV-seam positions while preserving per-loop UVs, then
    # close newly cut surfaces with a dark interior material. Exterior faces
    # are assigned exactly once, never removed merely for being disconnected.
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001)
    boundary=[e for e in bm.edges if e.is_boundary]
    cap_faces=bmesh.ops.holes_fill(bm,edges=boundary,sides=0).get('faces',[]) if boundary else []
    for f in cap_faces:f.material_index=1;f.smooth=False
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj=bpy.data.objects.new('SM_WardenHQ_'+name,mesh)
    scene.collection.objects.link(obj);parts[name]=obj
    points=[v.co for v in mesh.vertices]
    lo=[min(v[i] for v in points) for i in range(3)]
    hi=[max(v[i] for v in points) for i in range(3)]
    audit_parts[name]={'name':obj.name,'triangles':len(mesh.polygons),
        'source_faces':len(face_ids),'cap_faces_before_triangulation':len(cap_faces),
        'bounds_cm':[[lo[0],-hi[1],lo[2]],[hi[0],-lo[1],hi[2]]],
        'blender_rh_bounds_cm':[lo,hi],'uv_layers':len(mesh.uv_layers)}
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    # Keep the appearance-preserving RH mesh. Unreal must perform its native
    # Y reflection into LH coordinates; an extra export reflection mirrors the
    # visible shoulder/weapon side. Manifest UE landmarks reflect Y separately.
    bpy.ops.export_scene.fbx(filepath=str(OUT/(obj.name+'.fbx')),use_selection=True,
        object_types={'MESH'},use_space_transform=False,axis_forward='X',axis_up='Z',
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',global_scale=1,
        bake_space_transform=False,add_leaf_bones=False,bake_anim=False,
        use_mesh_modifiers=True,mesh_smooth_type='FACE',path_mode='STRIP')

bpy.data.objects.remove(src,do_unlink=True)
for o in list(scene.objects):
    if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
for filename in ['warden_pbr.glb','pbr_albedo_texture.png','pbr_mr_texture.png']:
    shutil.copy2(SOURCE/filename,OUT/filename)
for image in bpy.data.images:
    if image.source=='FILE':image.pack()
manifest={
    'source':str(SOURCE/'warden_pbr.glb'),
    'source_sha256':hashlib.sha256((SOURCE/'warden_pbr.glb').read_bytes()).hexdigest(),
    'original_triangles':input_tris,'simplified_exterior_triangles':reduced_tris,
    'total_segment_triangles':sum(p['triangles'] for p in audit_parts.values()),
    'coordinate_contract':'Blender inspection and FBX use RH centimeter coordinates, X forward and character right -Y. Unreal FBX importer performs mandatory RH-to-LH Y reflection; do not compensate it. Manifest joints_cm and bounds_cm use final UE LH centimeters, X forward, character right +Y, Z up. All origins zero. Import convert_scene=False,convert_scene_unit=False,import_uniform_scale=1,transform_vertex_to_absolute=True; component scale1.',
    'fbx_export_handedness':'Export unchanged normalized RH mesh. Native UE import maps (x,y,z) to (x,-y,z), preserving approved visible handedness. No extra reflection or reversed winding at export.',
    'source_to_ue':{'source_front':'-Y','center_source_x':center_x,'source_feet_z':feet_z,'cm_per_source_unit':scale,'mapping':'(-source.y, .105-source.x, source.z+.8940808176994324)*143.30669732583596'},
    'body_height_cm':270,
    'small_island_faces_reassigned_without_removal':reassigned,
    'joints_cm':{k:to_unreal_lh(v) for k,v in joints.items()},
    'blender_rh_joints_cm':{k:list(v) for k,v in joints.items()},
    'parts':audit_parts,
    'textures':{'base_color':'pbr_albedo_texture.png','metallic_roughness':'pbr_mr_texture.png','roughness_channel':'G','metallic_channel':'B','base_color_srgb':True,'metallic_roughness_srgb':False},
    'limitations':['Rigid segment articulation is a playable adaptation, not a production skeletal rig.','Fingers remain part of forearm mesh; only hammer is separated.','Static skirt can intersect legs at exaggerated angles.','Dark caps conceal cut interiors; prototype seams may show at close range.'],
}
(OUT/'warden_manifest.json').write_text(json.dumps(manifest,indent=2))

# Reproducible local inspection only. Meters-independent lighting is tuned
# for the deliberately centimeter-coordinate geometry; nothing here exports.
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1050;scene.render.resolution_y=1300
scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Inspection studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.22,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
target=Vector((0,0,135))
for name,loc,power,size in [('Key',(380,-400,550),28000000,380),('Fill',(330,360,300),16000000,300),('Rim',(-250,50,480),32000000,320)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;aim(o,target)
camdata=bpy.data.cameras.new('InspectionCamera');cam=bpy.data.objects.new('InspectionCamera',camdata)
scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=345;camdata.clip_end=5000
cam.location=(700,-200,180);aim(cam,target)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'WardenHQ_Prepared.blend'))
for view,loc in [('rest_front',(800,0,165)),('rest_threequarter',(700,-270,185))]:
    cam.location=loc;aim(cam,target);scene.render.filepath=str(OUT/(view+'.png'));bpy.ops.render.render(write_still=True)

# Pose preview uses the same rigid transform principle as game-side mapping:
# native segment axes are rotated to targets without stretching any armor.
def segment(name,start,end,newstart,newend):
    a,b=joints[start],joints[end]
    aa,bb=Vector(newstart),Vector(newend)
    q=(b-a).normalized().rotation_difference((bb-aa).normalized())
    parts[name].matrix_world=Matrix.Translation(aa)@q.to_matrix().to_4x4()@Matrix.Translation(-a)
rs=joints['RightShoulder'];re=rs+Vector((-17,-8,35));rh=re+Vector((-8,-4,48))
segment('RightUpperArm','RightShoulder','RightElbow',rs,re)
segment('RightForearm','RightElbow','RightHand',re,rh)
segment('Hammer','HammerGrip','HammerHead',rh,rh+Vector((-30,0,104)))
for side,angle in [('Right',-12),('Left',12)]:
    hip=joints[side+'Hip'];knee=joints[side+'Knee']
    hip_rotation=Matrix.Translation(hip)@Matrix.Rotation(math.radians(angle),4,'Y')@Matrix.Translation(-hip)
    bend=Matrix.Translation(knee)@Matrix.Rotation(math.radians(7),4,'Y')@Matrix.Translation(-knee)
    parts[side+'Thigh'].matrix_world=hip_rotation
    parts[side+'Shin'].matrix_world=hip_rotation@bend
    parts[side+'Foot'].matrix_world=hip_rotation@bend
cam.location=(800,-330,240);target=Vector((0,0,210));aim(cam,target);camdata.ortho_scale=470
scene.render.filepath=str(OUT/'pose_windup_walk.png');bpy.ops.render.render(write_still=True)
print('WARDEN_PREPARED',json.dumps(manifest))
