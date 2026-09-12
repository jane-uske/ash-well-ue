"""Prepare licensed existing plant meshes for instancing; retain original downloads."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedReferenceProduction';V=O/'Vegetation';report={}

def export(source,name,scale=100,triangle_limit=None):
    obj=source.copy();obj.data=source.data.copy();bpy.context.collection.objects.link(obj);obj.name=name
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    obj.parent=None;obj.matrix_world=Matrix.Identity(4)
    for m in list(obj.modifiers):obj.modifiers.remove(m)
    points=[v.co for v in obj.data.vertices]
    low=Vector([min(v[i] for v in points) for i in range(3)]);high=Vector([max(v[i] for v in points) for i in range(3)])
    anchor=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    obj.data.transform(Matrix.Scale(scale,4)@Matrix.Translation(-anchor))
    triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
    if triangle_limit and triangles>triangle_limit:
        # The older library mesh carries attributes from its Geometry Nodes
        # export. Validate that data before Blender's native BMesh reduction.
        obj.data.validate(clean_customdata=True)
        for attr in list(obj.data.attributes):
            if attr.name not in ({layer.name for layer in obj.data.uv_layers}|{'material_index'}) and not attr.is_required:
                obj.data.attributes.remove(attr)
        print('REDUCING',name,triangles,flush=True)
        m=obj.modifiers.new('Reference render budget','DECIMATE');m.ratio=triangle_limit/triangles;m.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=m.name)
    colors=obj.data.color_attributes.new(name='WindWeight',type='BYTE_COLOR',domain='POINT')
    max_z=max(v.co.z for v in obj.data.vertices)
    for v,c in zip(obj.data.vertices,colors.data):
        weight=max(0,min(1,v.co.z/max_z))**2
        c.color=(1,1,1,weight)
    obj.data.color_attributes.active_color=colors
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
    bpy.ops.export_scene.fbx(filepath=str(O/(name+'.fbx')),use_selection=True,object_types={'MESH'},
        axis_forward='X',axis_up='Z',use_space_transform=False,add_leaf_bones=False,bake_anim=False,
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',mesh_smooth_type='FACE')
    report[name]={'source_object':source.name,'triangles_before':triangles,
                  'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),
                  'materials':[m.name for m in obj.data.materials],
                  'faces_per_material':{str(i):sum(p.material_index==i for p in obj.data.polygons) for i in range(len(obj.data.materials))},
                  'wind_weight':'vertex alpha, rooted quadratic height'}
    if len(obj.data.materials)>1:assert all(report[name]['faces_per_material'].values()),'A material assignment was lost during reduction'
    bpy.data.objects.remove(obj,do_unlink=True)

bpy.ops.wm.open_mainfile(filepath=str(V/'grass_medium_01/grass_medium_01_2k.blend'))
for source,name in [('grass_medium_01_geonodes_tall_a_LOD0','SM_ReferenceGrassTall'),
                    ('grass_medium_01_geonodes_mid_b_LOD2','SM_ReferenceGrassMid'),
                    ('grass_medium_01_geonodes_large_a_LOD2','SM_ReferenceGrassDense')]:
    export(bpy.data.objects[source],name)
bpy.ops.wm.open_mainfile(filepath=str(V/'jacaranda_tree/jacaranda_tree_2k.blend'))
export(bpy.data.objects['jacaranda_tree_LOD1'],'SM_ReferenceBroadleaf',triangle_limit=200000)
source=bpy.data.objects['jacaranda_tree_geometry_nodes'];bare=source.copy();bare.data=source.data.copy();bpy.context.collection.objects.link(bare)
export(bare,'SM_ReferenceBareTree',triangle_limit=50000);bpy.data.objects.remove(bare,do_unlink=True)
(O/'vegetation-preparation.json').write_text(json.dumps(report,indent=2));print('VEGETATION_READY',json.dumps(report))
