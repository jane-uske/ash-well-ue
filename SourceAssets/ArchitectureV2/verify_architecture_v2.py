"""FBX round-trip verification; does not substitute for a real Unreal screenshot."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'architecture_v2_manifest.json').read_text())
report=[]
for chunk in manifest['chunks']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/chunk['file']),use_custom_normals=True)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(objects)==1,(chunk['name'],'mesh count',len(objects))
    obj=objects[0];mesh=obj.data;co=[obj.matrix_world@v.co for v in mesh.vertices]
    bounds={a:[fn(v[k] for v in co) for k in range(3)] for a,fn in [('min',min),('max',max)]}
    error=max(abs(bounds[a][k]-chunk['bounds_m'][a][k]) for a in ['min','max'] for k in range(3))
    assert error<.005,(chunk['name'],'coordinate error',error)
    assert len(mesh.uv_layers)>0,(chunk['name'],'UV absent')
    assert all(math.isfinite(q) for loop in mesh.uv_layers[0].data for q in loop.uv),(chunk['name'],'invalid UV')
    materials=[m.name.split('.')[0] for m in mesh.materials]
    assert materials==manifest['material_slots'],(chunk['name'],'material slots',materials)
    assert all(p.area>1e-14 for p in mesh.polygons),(chunk['name'],'degenerate face')
    assert obj.location.length<.001,(chunk['name'],'pivot')
    report.append({'name':chunk['name'],'coordinate_error_m':error,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'smooth_face_ratio':sum(p.use_smooth for p in mesh.polygons)/len(mesh.polygons),'uv_layers':len(mesh.uv_layers),'result':'pass'})
result={'result':'pass','scope':'Blender FBX roundtrip structural integrity; Unreal render is a separate check','chunk_count':len(report),'triangles':manifest['triangles'],'checks':report}
(ROOT/'architecture_v2_verification.json').write_text(json.dumps(result,indent=2))
print('ALL ROUNDTRIP PASS',len(report),flush=True)
