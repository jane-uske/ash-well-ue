import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='/Game/AshWell/Chapter01';ed=u.EditorAssetLibrary;assets=u.AssetToolsHelpers.get_asset_tools();mel=u.MaterialEditingLibrary
M={k:ed.load_asset(v) for k,v in {'Steel':'/Game/AshWell/Materials/V2/M_OldSteel','Rust':'/Game/AshWell/Materials/V2/M_Rust','Stone':'/Game/AshWell/Materials/V2/M_Concrete','Dark':'/Game/AshWell/Materials/M_DarkSteel','Amber':'/Game/AshWell/Materials/M_Amber'}.items()}
cloth=ed.load_asset(BASE+'/M_Cloth') or assets.create_asset('M_Cloth',BASE,u.Material,u.MaterialFactoryNew());mel.delete_all_material_expressions(cloth)
c=mel.create_material_expression(cloth,u.MaterialExpressionConstant3Vector);c.constant=u.LinearColor(.16,.11,.055,1);mel.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
q=mel.create_material_expression(cloth,u.MaterialExpressionConstant);q.r=.9;mel.connect_material_property(q,'',u.MaterialProperty.MP_ROUGHNESS);cloth.set_editor_property('two_sided',True);mel.recompile_material(cloth);ed.save_loaded_asset(cloth);M['Cloth']=cloth
manifest=json.loads((R/'SourceAssets/Chapter01/manifest.json').read_text());report={'meshes':[]}
for entry in manifest['meshes']:
 name=entry['name'];opt=u.FbxImportUI()
 for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,'import_as_skeletal':False,'import_materials':False,'import_textures':False}.items():opt.set_editor_property(k,v)
 for k,v in {'convert_scene':False,'convert_scene_unit':False,'transform_vertex_to_absolute':True,'combine_meshes':True,'auto_generate_collision':False,'generate_lightmap_u_vs':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():opt.static_mesh_import_data.set_editor_property(k,v)
 t=u.AssetImportTask();t.filename=str(R/'SourceAssets/Chapter01'/(name+'.fbx'));t.destination_path=BASE+'/Meshes';t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.options=opt;t.factory=u.FbxFactory();assets.import_asset_tasks([t])
 mesh=ed.load_asset(BASE+'/Meshes/'+name);assert mesh
 for i,slot in enumerate(mesh.static_materials):
  slot_name=str(slot.get_editor_property('material_slot_name'));key=next(k for k in M if slot_name.startswith('AWC_'+k));mesh.set_material(i,M[key])
 
 if name=='SM_C1_DepartureGate':
  sub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);sub.remove_collisions(mesh);sub.add_simple_collisions(mesh,u.ScriptingCollisionShapeType.BOX)
 ed.save_loaded_asset(mesh);report['meshes'].append({'name':name,'bounds':str(mesh.get_bounds().box_extent)})
report['ok']=True;(R/'Saved/Chapter01/import.json').write_text(json.dumps(report,indent=2))
