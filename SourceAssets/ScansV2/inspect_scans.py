import bpy, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
report=[]
for aid in ['rock_face_01','boulder_01']:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(root/aid/(aid+'_4k.fbx')))
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH': continue
        pts=[o.matrix_world@Vector(v) for v in o.bound_box]
        report.append({'id':aid,'object':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)],'verts':len(o.data.vertices),'uv':[uv.name for uv in o.data.uv_layers]})
print('SCAN_REPORT '+json.dumps(report,indent=2))
(root/'bounds.json').write_text(json.dumps(report,indent=2))
