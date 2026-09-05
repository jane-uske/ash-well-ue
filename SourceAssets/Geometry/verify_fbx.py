"""Blender FBX round-trip structural check; not an Unreal render test."""
import bpy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'environment_manifest.json').read_text())
report=[]
for chunk in manifest['chunks']:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/chunk['file']),use_custom_normals=True)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(meshes)==1,(chunk['name'],len(meshes))
    obj=meshes[0]; mesh=obj.data
    coords=[obj.matrix_world@v.co for v in mesh.vertices]
    bounds={'min':[min(v[k] for v in coords) for k in range(3)],'max':[max(v[k] for v in coords) for k in range(3)]}
    error=max(abs(bounds[a][k]-chunk['bounds_m'][a][k]) for a in ['min','max'] for k in range(3))
    assert error<.005,(chunk['name'],'coordinate round-trip',error)
    assert len(mesh.uv_layers)>=1,(chunk['name'],'missing UV')
    assert all(math.isfinite(x) for loop in mesh.uv_layers[0].data for x in loop.uv),(chunk['name'],'invalid UV')
    materials=[m.name.split('.')[0] for m in mesh.materials]
    assert materials==manifest['materials'],(chunk['name'],materials)
    assert all(p.area>1e-14 for p in mesh.polygons),(chunk['name'],'degenerate faces')
    smooth_ratio=sum(p.use_smooth for p in mesh.polygons)/len(mesh.polygons)
    if chunk['name'] in manifest.get('rock_refinement',{}).get('changed_chunks',[]):
        assert smooth_ratio>.95,(chunk['name'],'missing smooth shading',smooth_ratio)
    report.append({'name':chunk['name'],'roundtrip_max_error_m':error,'uv_layers':len(mesh.uv_layers),'smooth_face_ratio':smooth_ratio,'material_slots':materials,'result':'pass'})
(ROOT/'fbx_verification.json').write_text(json.dumps({'scope':'Blender FBX roundtrip only; Unreal import/render must also be verified','chunks':report,'result':'pass'},indent=2))
print('ROUNDTRIP PASS',len(report),flush=True)
