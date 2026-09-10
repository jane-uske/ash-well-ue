import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='/Game/AshWell/Combat/PlayerHammer';ed=u.EditorAssetLibrary;tools=u.AssetToolsHelpers.get_asset_tools();mel=u.MaterialEditingLibrary
mats={}
for n,c,metal,rough in [('Steel',(.07,.09,.10),.85,.62),('Edge',(.30,.34,.35),.95,.40),('Rubber',(.012,.017,.019),0,.9),('Ochre',(.34,.17,.035),.55,.65)]:
 name='M_PlayerHammer_'+n;mat=ed.load_asset(BASE+'/'+name)
 if not mat:mat=tools.create_asset(name,BASE,u.Material,u.MaterialFactoryNew())
 mel.delete_all_material_expressions(mat)
 col=mel.create_material_expression(mat,u.MaterialExpressionConstant3Vector);col.constant=u.LinearColor(*c,1);mel.connect_material_property(col,'',u.MaterialProperty.MP_BASE_COLOR)
 for value,prop in [(metal,u.MaterialProperty.MP_METALLIC),(rough,u.MaterialProperty.MP_ROUGHNESS)]:
  q=mel.create_material_expression(mat,u.MaterialExpressionConstant);q.r=value;mel.connect_material_property(q,'',prop)
 if n!='Rubber':
  rough_tex=ed.load_asset('/Game/AshWell/Textures/V2/T_rusty_metal_04_roughness')
  sample=mel.create_material_expression(mat,u.MaterialExpressionTextureSample);sample.texture=rough_tex;sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
  scale=mel.create_material_expression(mat,u.MaterialExpressionMultiply);scale.set_editor_property('const_b',.28);mel.connect_material_expressions(sample,'R',scale,'A')
  bias=mel.create_material_expression(mat,u.MaterialExpressionAdd);bias.set_editor_property('const_b',max(.25,rough-.18));mel.connect_material_expressions(scale,'',bias,'A');mel.connect_material_property(bias,'',u.MaterialProperty.MP_ROUGHNESS)
 mel.recompile_material(mat);ed.save_loaded_asset(mat);mats[n]=mat
if not globals().get('MATERIALS_ONLY',False):
 report=[]
 for name in ['SM_PlayerHammer_Handle','SM_PlayerHammer_Head']:
  opts=u.FbxImportUI()
  for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():opts.set_editor_property(k,v)
  for k,v in {'convert_scene':False,'convert_scene_unit':False,'force_front_x_axis':False,'import_rotation':u.Rotator(0,0,0),'import_translation':u.Vector(0,0,0),'import_uniform_scale':1.0,'transform_vertex_to_absolute':True,'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():opts.static_mesh_import_data.set_editor_property(k,v)
  existing=ed.load_asset(BASE+'/'+name)
  if existing and isinstance(existing.get_editor_property('asset_import_data'),u.FbxStaticMeshImportData):
   data=existing.get_editor_property('asset_import_data')
   for key in ['convert_scene','convert_scene_unit','force_front_x_axis','import_rotation','import_translation','import_uniform_scale']:
    data.set_editor_property(key,opts.static_mesh_import_data.get_editor_property(key))
  t=u.AssetImportTask();t.filename=str(R/'SourceAssets/PlayerHammer'/(name+'.fbx'));t.destination_path=BASE;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opts;t.factory=u.FbxFactory();tools.import_asset_tasks([t])
  mesh=ed.load_asset(BASE+'/'+name);assert mesh
  for i,s in enumerate(mesh.static_materials):
   slot=str(s.get_editor_property('material_slot_name'));key=next(k for k in mats if k in slot);mesh.set_material(i,mats[key])
  b=mesh.get_bounds()
  if name.endswith('Handle'):assert b.origin.y>20 and b.box_extent.y<34,(b.origin,b.box_extent)
  else:assert 12<b.box_extent.x<15,(b.origin,b.box_extent)
  ed.save_loaded_asset(mesh);report.append({'name':name,'center':str(b.origin),'extent':str(b.box_extent)})
 (R/'Saved/Polish/player-hammer-import.json').write_text(json.dumps(report,indent=2))
