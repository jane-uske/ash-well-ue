"""Fresh FBX roundtrip and a Blender-only material/geometry preview, not UE QA."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'surface_manifest.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report=[]
for entry in manifest['assets']:
    bpy.ops.import_scene.fbx(filepath=str(ROOT/entry['file']),use_custom_normals=True)
    objects=[o for o in bpy.context.selected_objects if o.type=='MESH']
    assert len(objects)==1,(entry['file'],len(objects))
    obj=objects[0];obj.data.calc_loop_triangles()
    triangles=len(obj.data.loop_triangles)
    assert triangles==entry['triangles'],(entry['file'],triangles,entry['triangles'])
    coords=[obj.matrix_world@v.co for v in obj.data.vertices]
    bounds={'min':[min(v[k] for v in coords) for k in range(3)],'max':[max(v[k] for v in coords) for k in range(3)]}
    for key in ['min','max']:
        for k in range(3):assert abs(bounds[key][k]-entry['bounds_m'][key][k])<.00001
    assert len(obj.data.uv_layers)>0
    assert len(obj.data.color_attributes)>0
    slots=[m.name.split('.')[0] for m in obj.data.materials]
    assert slots==manifest['material_slots'],(entry['file'],slots)
    report.append({'file':entry['file'],'triangles':triangles,'bounds_m':bounds,'material_slots':slots,'uv_layers':len(obj.data.uv_layers),'vertex_color_attributes':len(obj.data.color_attributes),'pass':True})
(ROOT/'verification.json').write_text(json.dumps({'scope':'Fresh Blender FBX import only; no Unreal import or render claims.','result':'pass','assets':report},indent=2)+'\n')

textures=json.loads((ROOT/'texture_manifest.json').read_text())
tex={x['material_name']:x for x in textures['materials']}
for obj in [o for o in bpy.data.objects if o.type=='MESH']:
    for m in obj.data.materials:
        name=m.name.split('.')[0]
        m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
        bsdf=next(x for x in n if x.type=='BSDF_PRINCIPLED')
        spec=tex['OldSteel' if name=='DarkSteel' else 'WetStone']
        uv=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=.5
        l.new(uv.outputs['UV'],mapping.inputs[0])
        def image_node(channel,srgb=False):
            node=n.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/spec['textures'][channel]['path']),check_existing=True)
            if not srgb:node.image.colorspace_settings.name='Non-Color'
            l.new(mapping.outputs[0],node.inputs['Vector']);return node
        base=image_node('base_color',True)
        hsv=n.new('ShaderNodeHueSaturation');hsv.inputs['Saturation'].default_value=.2;hsv.inputs['Value'].default_value=.45 if name=='WetStone' else .25
        l.new(base.outputs['Color'],hsv.inputs['Color']);l.new(hsv.outputs['Color'],bsdf.inputs['Base Color'])
        rough=image_node('roughness');mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY_ADD';mul.inputs[1].default_value=.7;mul.inputs[2].default_value=.08 if name=='WetStone' else .22
        l.new(rough.outputs['Color'],mul.inputs[0]);l.new(mul.outputs[0],bsdf.inputs['Roughness'])
        normal=image_node('normal');sep=n.new('ShaderNodeSeparateColor');sep.mode='RGB';l.new(normal.outputs['Color'],sep.inputs['Color'])
        inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;l.new(sep.outputs['Green'],inv.inputs[1])
        comb=n.new('ShaderNodeCombineColor');comb.mode='RGB';l.new(sep.outputs['Red'],comb.inputs['Red']);l.new(inv.outputs[0],comb.inputs['Green']);l.new(sep.outputs['Blue'],comb.inputs['Blue'])
        nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65;l.new(comb.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
        bsdf.inputs['Metallic'].default_value=.55 if name=='DarkSteel' else 0

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.world.color=(.2,.2,.2)
bpy.ops.object.camera_add(location=(-3.75,3.5,2.5));cam=bpy.context.object
cam.rotation_euler=(Vector((3.5,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=38;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(0,1.5,5));lamp=bpy.context.object;lamp.data.energy=850;lamp.data.shape='DISK';lamp.data.size=5;lamp.data.color=(.55,.7,1)
bpy.ops.object.light_add(type='POINT',location=(0,-.8,.5));lamp=bpy.context.object;lamp.data.energy=55;lamp.data.color=(1,.42,.13);lamp.data.shadow_soft_size=.07
scene.render.filepath=str(ROOT/'preview_surface_v2.png')
bpy.ops.render.render(write_still=True)
print('Verified and previewed',flush=True)
