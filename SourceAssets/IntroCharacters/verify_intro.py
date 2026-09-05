from pathlib import Path
import bpy,json,math
from mathutils import Vector
OUT=Path(__file__).resolve().parent
manifest=json.loads((OUT/'manifest.json').read_text())
reports=[]
for asset in manifest['assets']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(OUT/asset['skeletal_mesh']),use_anim=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    assert len(meshes)==1 and len(rigs)==1,(meshes,rigs)
    mesh=meshes[0];rig=rigs[0]
    points=[mesh.matrix_world@v.co for v in mesh.data.vertices]
    bounds=[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
    unweighted=sum(1 for v in mesh.data.vertices if not v.groups)
    weight_error=max(abs(sum(g.weight for g in v.groups)-1.) for v in mesh.data.vertices)
    assert unweighted==0 and weight_error<1e-5,(unweighted,weight_error)
    assert 1.7<bounds[1][2]-bounds[0][2]<1.9,bounds
    assert len(rig.data.bones)==24,len(rig.data.bones)
    assert len(mesh.data.materials)==6
    reports.append({'mesh':asset['skeletal_mesh'],'vertices':len(mesh.data.vertices),
        'bones':len(rig.data.bones),'bounds_m':bounds,'unweighted_vertices':unweighted,
        'max_weight_sum_error':weight_error,'uv_layers':[x.name for x in mesh.data.uv_layers],
        'materials':[x.name for x in mesh.data.materials]})
    for clip in asset['animations']:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.fbx(filepath=str(OUT/clip['file']),use_anim=True)
        ar=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'][0]
        action=ar.animation_data.action
        start,end=map(float,action.frame_range)
        assert abs((end-start)/bpy.context.scene.render.fps-clip['duration_seconds'])<.04,(clip,start,end,bpy.context.scene.render.fps)
        positions=[]
        for frame in range(round(start),round(end)+1):
            bpy.context.scene.frame_set(frame)
            positions.append(tuple(ar.pose.bones['root'].head))
        movement=max((Vector(p)-Vector(positions[0])).length for p in positions)
        assert movement<1e-5,movement
        reports.append({'clip':clip['file'],'imported_frames':[start,end],
            'fps':bpy.context.scene.render.fps,'root_drift_m':movement,'bones':len(ar.data.bones)})
(OUT/'verification.json').write_text(json.dumps({'status':'PASS','checks':reports},indent=2)+'\n')
print('INTRO_VERIFICATION_PASS '+json.dumps(reports))
