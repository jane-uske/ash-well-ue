"""Read exported FBX meshes back with Blender and check the delivered geometry."""
from pathlib import Path
import bpy, json, math

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
results=[]
for entry in manifest['assets']:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(root/entry['fbx']))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==1, 'Exactly one combined mesh per character is expected.'
    obj=meshes[0]
    coords=[obj.matrix_world@v.co for v in obj.data.vertices]
    assert all(math.isfinite(c) for p in coords for c in p)
    bounds=[[min(p[i] for p in coords) for i in range(3)], [max(p[i] for p in coords) for i in range(3)]]
    assert all(abs(a-b)<0.0001 for aa,bb in zip(bounds,entry['bounds_m']) for a,b in zip(aa,bb)),(bounds,entry['bounds_m'])
    slots=[m.name.split('.')[0] for m in obj.data.materials]
    assert slots==entry['material_slots'], slots
    triangles=sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
    assert triangles==entry['triangles'],(triangles,entry['triangles'])
    assert obj.data.uv_layers, 'UV layer must survive export.'
    results.append({'fbx':entry['fbx'],'triangles':triangles,'bounds_m':bounds,'material_slots':slots,'uv_layer_count':len(obj.data.uv_layers),'passed':True})
assert sum(r['triangles'] for r in results)<=300000
(root/'verification.json').write_text(json.dumps({'roundtrip':'Blender FBX export and fresh Blender FBX import; not a UE import/render test','results':results},indent=2)+'\n')
print('EXPEDITION_FBX_CHECKS_PASS '+json.dumps(results))
