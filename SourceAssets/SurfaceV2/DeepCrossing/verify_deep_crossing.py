import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text());result=[]
for item in manifest['assets']:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.fbx(filepath=str(ROOT/item['file']),use_custom_normals=True)
 obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(obs)==1
 o=obs[0];o.data.calc_loop_triangles();assert len(o.data.loop_triangles)==item['triangles']
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 bounds={k:[fn(p[i] for p in pts) for i in range(3)] for k,fn in [('min',min),('max',max)]}
 for k in ['min','max']:
  for i in range(3):assert abs(bounds[k][i]-item['bounds_m'][k][i])<.00002
 slots=[m.name.split('.')[0] for m in o.data.materials];assert slots==manifest['material_slots']
 assert len(o.data.uv_layers)>0
 result.append({'file':item['file'],'triangles':item['triangles'],'bounds':bounds,'slots':slots,'pass':True})
(ROOT/'verification.json').write_text(json.dumps({'scope':'Independent Blender FBX reimport only; UE import and visual framing remain parent checks.','result':'pass','assets':result},indent=2)+'\n')
print('DEEP CROSSING PASS')
