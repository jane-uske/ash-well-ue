"""Prepare only requested Poly Haven scan meshes; source files stay read-only.

Run in Blender background mode. Outputs are confined to Prepared/.
"""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'Prepared';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=json.loads((ROOT/'manifest.json').read_text())
specs=[('rock_face_01','rock_face_01','SM_Scan_RockFace01'),
       ('boulder_01','boulder_01_LOD0','SM_Scan_Boulder01_LOD0')]
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1.0
records=[]

def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

def bounds(obj):
    pts=[obj.matrix_world@v.co for v in obj.data.vertices]
    return {'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)]}

def sorted_uvs(obj):
    return sorted((round(v.uv.x,5),round(v.uv.y,5)) for v in obj.data.uv_layers.active.data)

def render_orientation(obj,aid):
    """Small inspection images; not Unreal render results."""
    src=next(x for x in SOURCE['assets'] if x['id']==aid)
    mat=bpy.data.materials.new('Scan inspection');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links
    bsdf=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    bc=n.new('ShaderNodeTexImage');bc.image=bpy.data.images.load(str(ROOT/src['textures']['base_color']['path']),check_existing=True)
    l.new(bc.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.8
    obj.data.materials.clear();obj.data.materials.append(mat)
    for f in obj.data.polygons:f.material_index=0
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16
    scene.render.resolution_x=720;scene.render.resolution_y=600;scene.render.resolution_percentage=100
    scene.world.color=(.15,.15,.15)
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=9;scene.camera=cam
    bpy.ops.object.light_add(type='AREA');lamp=bpy.context.object;lamp.data.energy=1700;lamp.data.shape='DISK';lamp.data.size=7
    target=Vector((0,1.2,2.1))
    for side,pos in [('from_minus_y',(0,-15,7)),('from_plus_y',(0,17,7))]:
        cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        lamp.location=Vector(pos)+Vector((-3,0,3));lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(aid+'_'+side+'.png'));bpy.ops.render.render(write_still=True)

for aid,selected,export_name in specs:
    clear();src=next(x for x in SOURCE['assets'] if x['id']==aid)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/src['mesh']['path']),use_custom_normals=True)
    choices=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name==selected]
    assert len(choices)==1,(aid,[o.name for o in bpy.context.scene.objects])
    obj=choices[0]
    for other in list(bpy.context.scene.objects):
        if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    uv_before=sorted_uvs(obj);before=bounds(obj)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    assert sorted_uvs(obj)==uv_before
    obj.name=export_name;obj.data.name=export_name
    after=bounds(obj)
    for k in ['min','max']:
        for i in range(3):assert abs(before[k][i]-after[k][i])<1e-5
    obj.data.calc_loop_triangles()
    bins={k:0. for k in ['+X','-X','+Y','-Y','+Z','-Z']}
    area=0
    for face in obj.data.polygons:
        face_area=face.area;area+=face_area
        a=max(range(3),key=lambda i:abs(face.normal[i]));direction=('+' if face.normal[a]>=0 else '-')+'XYZ'[a]
        bins[direction]+=face_area
    path=OUT/(export_name+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
        global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,
        mesh_smooth_type='FACE',use_mesh_modifiers=False,use_triangles=False,use_tspace=True,
        add_leaf_bones=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
    record={'id':aid,'selected_source_object':selected,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'vertices':len(obj.data.vertices),'triangles':len(obj.data.loop_triangles),'bounds_m':after,'origin_m':list(obj.location),
        'rotation_radians':list(obj.rotation_euler),'scale':list(obj.scale),'material_slots':[m.name for m in obj.data.materials],
        'uv_layers':[uv.name for uv in obj.data.uv_layers],'uv_changed':False,
        'normal_convention':'Original geometry winding and custom normals preserved. Source DirectX normal texture untouched; Unreal FlipGreenChannel=False.',
        'dominant_normal_surface_area_m2':bins,'total_surface_area_m2':area,
        'texture_paths':{k:'../'+v['path'] for k,v in src['textures'].items()},'source_page':src['source'],'license':'CC0'}
    # Independent re-import verifies normalized export and preserves the chosen LOD.
    original_uv=sorted_uvs(obj);original_triangles=record['triangles']
    clear();bpy.ops.import_scene.fbx(filepath=str(path),use_custom_normals=True)
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==1
    obj=imported[0];obj.data.calc_loop_triangles();again=bounds(obj)
    assert len(obj.data.loop_triangles)==original_triangles
    assert sorted_uvs(obj)==original_uv
    for k in ['min','max']:
        for i in range(3):assert abs(after[k][i]-again[k][i])<1e-5
    record['roundtrip_validation']='PASS: one mesh, chosen source LOD, equal triangle count, UV coordinate multiset, and world bounds.'
    records.append(record)
    if aid=='rock_face_01':render_orientation(obj,aid)
    print('PREPARED',json.dumps(record),flush=True)

(OUT/'manifest.json').write_text(json.dumps({'units':'metres','axes':'Authored source X/Y/Z preserved; FBX axis_forward=-Y, axis_up=Z, scale_length=1, FBX_SCALE_UNITS.',
    'placement':'No scene placement, mirroring, centering, or height adjustment applied. Every normalized object is at world origin with identity transforms.',
    'source_files_modified':False,'source_manifest':'../manifest.json','assets':records,
    'inspection_images':'rock_face_01_from_minus_y.png and rock_face_01_from_plus_y.png are Blender orientation checks, not Unreal renders.'},indent=2)+'\n')
print('COMPLETE',OUT/'manifest.json',flush=True)
