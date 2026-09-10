"""Create experiment-only polearm and saddle in a fresh background Blender.
No existing asset is modified. Run with Blender --background --factory-startup.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'SourceAssets/MountedBoss'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.unit_settings.system = 'METRIC'
s.unit_settings.scale_length = .01

def mat(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    return m

steel = mat('M_MountedSteel', (.12, .15, .16), .82, .35)
edge = mat('M_MountedEdge', (.31, .34, .34), .88, .27)
wood = mat('M_MountedWood', (.07, .027, .012), .0, .7)
leather = mat('M_MountedLeather', (.032, .015, .009), .0, .76)
brass = mat('M_MountedBrass', (.2, .11, .033), .72, .43)

def cylinder(name, a, b, radius, material, vertices=16):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                      depth=(b-a).length, location=(a+b)*.5)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b-a).to_track_quat('Z', 'Y')
    o.data.materials.append(material)
    bevel = o.modifiers.new('Small forged edge', 'BEVEL')
    bevel.width = .28
    bevel.segments = 2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o

def blade(name, polygon, halfthickness, material):
    n = len(polygon)
    verts = [(x, y, z) for y in (-halfthickness, halfthickness) for x,z in polygon]
    faces = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    s.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob

def join_export(name, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    bpy.context.scene.cursor.location = (0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/f'{name}.fbx'), use_selection=True,
        object_types={'MESH'}, bake_anim=False, use_space_transform=False,
        axis_forward='X', axis_up='Z', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE')
    return o

parts = [cylinder('Ash shaft', (-85,0,0), (153,0,0), 2.5, wood)]
parts += [cylinder('Steel socket', (112,0,0), (160,0,0), 3.3, steel)]
parts += [cylinder('Butt cap', (-85,0,0), (-76,0,0), 3, steel)]
parts += [cylinder('Grip leather', (-15,0,0), (25,0,0), 2.8, leather)]
for x in (-16,26,110,126,154):
    parts.append(cylinder('Brass collar', (x-1,0,0), (x+1,0,0), 3.6, brass))
parts += [blade('Spear point', [(153,-3),(195,0),(153,7)], 1.5, edge)]
parts += [blade('Axe cheek', [(124,2),(131,23),(128,36),(144,47),(166,43),(157,22),(154,3)], 2.0, steel)]
parts += [blade('Axe cutting edge', [(128,36),(144,47),(166,43),(169,47),(144,51),(125,39)], 1.1, edge)]
parts += [blade('Rear beak', [(134,-3),(137,-18),(125,-29),(143,-23),(151,-5)], 1.8, steel)]
halberd = join_export('SM_MountedHalberd', parts)

# Saddle origin is the centre of the seat. It follows the horse body bone.
parts = []
for name, location, scale, material in [
    ('Leather pad', (0,0,-6), (47,37,9), leather),
    ('Seat', (0,0,0), (27,24,5), wood),
    ('Pommel', (28,0,4), (5,25,10), leather),
    ('Cantle', (-31,0,5), (5,29,12), leather),
]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=location)
    o=bpy.context.object; o.name=name; o.scale=scale
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    parts.append(o)
for sign in (-1,1):
    parts.append(cylinder('Stirrup strap', (5,sign*30,-5), (12,sign*45,-59), 2, leather))
    parts.append(cylinder('Stirrup foot', (3,sign*45,-60), (22,sign*45,-60), 2, steel))
saddle=join_export('SM_MountedSaddle', parts)
saddle.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MountedProps.blend'))
(OUT/'props_manifest.json').write_text(json.dumps({
    'units':'centimetres','forward':'+X','polearm_grip':[0,0,0],
    'polearm_tip':[195,0,0],'polearm_butt':[-85,0,0],
    'polearm_blade_outer':[144,0,51],
    'saddle_origin':'seat centre; attach near horse back, z=175 cm world',
    'materials':{m.name:{'base_color':list(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value),
                            'metallic':m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value,
                            'roughness':m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value}
                 for m in [steel,edge,wood,leather,brass]},
    'status':'Experiment geometry; no paid generation'
},indent=2))
print('MOUNTED_PROPS_READY')
