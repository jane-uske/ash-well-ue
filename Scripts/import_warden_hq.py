"""Import only prepared meshes/textures; inspector cameras and lights are excluded."""
import json,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'SourceAssets/WardenHQ'
BASE='/Game/AshWell/Combat/WardenHQ'
ED=u.EditorAssetLibrary;TOOLS=u.AssetToolsHelpers.get_asset_tools();MEL=u.MaterialEditingLibrary
report={'state':'running'}
try:
    textures={}
    for filename,name,srgb in [('pbr_albedo_texture.png','T_WardenHQ_BaseColor',True),('pbr_mr_texture.png','T_WardenHQ_MR',False)]:
        t=u.AssetImportTask();t.filename=str(SRC/filename);t.destination_path=BASE;t.destination_name=name
        t.automated=True;t.replace_existing=True;t.save=True;t.factory=u.TextureFactory()
        TOOLS.import_asset_tasks([t]);tex=ED.load_asset(BASE+'/'+name);assert isinstance(tex,u.Texture2D)
        tex.set_editor_property('srgb',srgb)
        if not srgb:tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
        ED.save_loaded_asset(tex);textures[name]=tex
    mat=ED.load_asset(BASE+'/M_WardenHQ')
    if not mat:mat=TOOLS.create_asset('M_WardenHQ',BASE,u.Material,u.MaterialFactoryNew())
    MEL.delete_all_material_expressions(mat)
    albedo=MEL.create_material_expression(mat,u.MaterialExpressionTextureSample)
    albedo.texture=textures['T_WardenHQ_BaseColor'];albedo.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
    mr=MEL.create_material_expression(mat,u.MaterialExpressionTextureSample)
    mr.texture=textures['T_WardenHQ_MR'];mr.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
    assert MEL.connect_material_property(albedo,'RGB',u.MaterialProperty.MP_BASE_COLOR)
    assert MEL.connect_material_property(mr,'G',u.MaterialProperty.MP_ROUGHNESS)
    assert MEL.connect_material_property(mr,'B',u.MaterialProperty.MP_METALLIC)
    MEL.layout_material_expressions(mat);MEL.recompile_material(mat);ED.save_loaded_asset(mat)
    inner=ED.load_asset(BASE+'/M_WardenHQ_Inner')
    if not inner:inner=TOOLS.create_asset('M_WardenHQ_Inner',BASE,u.Material,u.MaterialFactoryNew())
    MEL.delete_all_material_expressions(inner)
    inner.set_editor_property('two_sided',True)
    for value,prop in [(0.025,u.MaterialProperty.MP_BASE_COLOR),(0.85,u.MaterialProperty.MP_ROUGHNESS),(0.2,u.MaterialProperty.MP_METALLIC)]:
        node=MEL.create_material_expression(inner,u.MaterialExpressionConstant);node.r=value
        assert MEL.connect_material_property(node,'',prop)
    MEL.recompile_material(inner);ED.save_loaded_asset(inner)
    meshes=[]
    sources=sorted(SRC.rglob('SM_WardenHQ_*.fbx'));assert len(sources)==12,len(sources)
    for source in sources:
        opts=u.FbxImportUI()
        for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():opts.set_editor_property(k,v)
        data=opts.static_mesh_import_data
        for k,v in {'convert_scene':False,'convert_scene_unit':False,'force_front_x_axis':False,'transform_vertex_to_absolute':True,'import_uniform_scale':1.0,'import_rotation':u.Rotator(0,0,0),'import_translation':u.Vector(0,0,0),'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False}.items():data.set_editor_property(k,v)
        data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        if ED.does_asset_exist(BASE+'/'+source.stem):assert ED.delete_asset(BASE+'/'+source.stem)
        task=u.AssetImportTask();task.filename=str(source);task.destination_path=BASE;task.destination_name=source.stem
        task.automated=True;task.replace_existing=True;task.replace_existing_settings=True;task.save=True;task.options=opts;task.factory=u.FbxFactory()
        TOOLS.import_asset_tasks([task]);mesh=ED.load_asset(BASE+'/'+source.stem);assert isinstance(mesh,u.StaticMesh)
        for i in range(len(mesh.get_editor_property('static_materials'))):mesh.set_material(i,mat if i==0 else inner)
        ED.save_loaded_asset(mesh)
        bounds=mesh.get_bounds();meshes.append({'asset':mesh.get_path_name(),'center':[bounds.origin.x,bounds.origin.y,bounds.origin.z],'extent':[bounds.box_extent.x,bounds.box_extent.y,bounds.box_extent.z]})
    manifest=json.loads((SRC/'warden_manifest.json').read_text())
    for part in manifest['parts'].values():
        actual=next(x for x in meshes if x['asset'].split('.')[-1]==part['name'])
        for axis in range(3):
            assert abs(actual['center'][axis]-actual['extent'][axis]-part['bounds_cm'][0][axis])<.02,(part['name'],'minimum',axis,actual)
            assert abs(actual['center'][axis]+actual['extent'][axis]-part['bounds_cm'][1][axis])<.02,(part['name'],'maximum',axis,actual)
    right=next(x for x in meshes if x['asset'].split('.')[-1]=='SM_WardenHQ_RightForearm')
    assert right['center'][1]>0, 'FBX handedness mismatch: approved right arm must have positive Y'
    body=next(x for x in meshes if x['asset'].split('.')[-1]=='SM_WardenHQ_Body')
    assert 260<body['center'][2]+body['extent'][2]<280, 'FBX unit/height mismatch'
    ED.save_directory(BASE,only_if_is_dirty=True,recursive=True)
    report={'state':'completed','meshes':meshes,'material':mat.get_path_name(),'channels':{'base_color':'sRGB RGB','roughness':'linear G','metallic':'linear B'},'camera_light_imported':False}
except Exception:
    report={'state':'failed','error':traceback.format_exc()};u.log_error(report['error'])
(ROOT/'Saved/Automation').mkdir(parents=True,exist_ok=True)
(ROOT/'Saved/Automation/warden-import-report.json').write_text(json.dumps(report,indent=2))
u.SystemLibrary.quit_editor()
