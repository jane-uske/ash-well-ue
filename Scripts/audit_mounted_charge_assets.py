"""Read-only source audit. Run in a disposable Blender background process.

Writes only the audit report; never saves or modifies imported source files.
"""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'Docs/Implementation/MountedBoss/ChargeSample/asset_audit.json'
SOURCES = {
    'knight': 'meshy_output/20260911_201322_gilded-sentinel_01a08e8e/rigged.glb',
    'horse': 'meshy_output/20260911_201320_gilded-warhorse_01a08f11/rigged.glb',
    'poleaxe': 'meshy_output/20260911_201214_tree-sentinel-halberd_87d0ac80/model.glb',
    'shield': 'meshy_output/20260911_201130_tree-sentinel-shield_cad64068/model.glb',
}
report = {'status': 'source audit only; no UE import or dynamic acceptance', 'assets': {}}
for label, relative in SOURCES.items():
    source = ROOT / relative
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    # The glTF importer creates bone display geometry. It is not source mesh.
    bone_shapes = {b.custom_shape for o in rigs for b in o.pose.bones if b.custom_shape}
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o not in bone_shapes]
    points = [o.matrix_world @ Vector(p) for o in meshes for p in o.bound_box]
    minimum = [min(p[i] for p in points) for i in range(3)]
    maximum = [max(p[i] for p in points) for i in range(3)]
    entry = {
        'source': relative, 'sha256': digest,
        'bounds_blender_meters': [minimum, maximum],
        'dimensions_cm': [(maximum[i] - minimum[i]) * 100 for i in range(3)],
        'meshes': [], 'rigs': [], 'materials': [],
        'images': [{'name': im.name, 'pixels': list(im.size)} for im in bpy.data.images],
        'actions': [a.name for a in bpy.data.actions],
        'named_attachment_objects': [o.name for o in bpy.context.scene.objects if o.type == 'EMPTY'],
    }
    for o in meshes:
        unweighted = sum(not any(g.weight > 0.00001 for g in v.groups) for v in o.data.vertices) if rigs else None
        entry['meshes'].append({
            'name': o.name, 'vertices': len(o.data.vertices),
            'triangles': sum(len(p.vertices) - 2 for p in o.data.polygons),
            'uv_layers': [l.name for l in o.data.uv_layers],
            'object_scale': list(o.scale), 'unweighted_vertices': unweighted,
            'vertex_groups': [g.name for g in o.vertex_groups],
        })
    for o in rigs:
        entry['rigs'].append({'name': o.name, 'object_scale': list(o.scale), 'bones': [
            {'name': b.name, 'parent': b.parent.name if b.parent else None,
             'head_m': list(o.matrix_world @ b.head_local),
             'tail_m': list(o.matrix_world @ b.tail_local)} for b in o.data.bones
        ]})
    for material in bpy.data.materials:
        links = []
        if material.use_nodes:
            links = [{'from': l.from_node.type, 'image': l.from_node.image.name if l.from_node.type == 'TEX_IMAGE' and l.from_node.image else None,
                      'to': l.to_node.type, 'input': l.to_socket.name} for l in material.node_tree.links]
        entry['materials'].append({'name': material.name, 'links': links})
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    report['assets'][label] = entry
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('AUDITED', label, json.dumps({k: entry[k] for k in ['dimensions_cm', 'images', 'actions']}), flush=True)
print('MOUNTED_CHARGE_ASSET_AUDIT', OUTPUT)
