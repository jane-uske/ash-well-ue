from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/BattlePolish';BASE='/Game/AshWell/Combat/BattlePolish';ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();ed.make_directory(BASE);report={'assets':[]}
for file in list(O.glob('SM_*.fbx'))+list(O.glob('AW_Battle_*.wav')):
 t=u.AssetImportTask();t.filename=str(file);t.destination_path=BASE;t.destination_name=file.stem;t.automated=True;t.save=True;t.replace_existing=True
 if file.suffix=='.fbx':
  opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_animations=False;opts.import_materials=False;opts.import_textures=False;opts.automated_import_should_detect_type=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
  opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.import_uniform_scale=1.;t.options=opts;t.factory=u.FbxFactory()
 at.import_asset_tasks([t]);asset=ed.load_asset(BASE+'/'+file.stem);assert asset,file;report['assets'].append(asset.get_path_name())
M=ed.load_asset(BASE+'/M_BattleGlow')
if not M:M=at.create_asset('M_BattleGlow',BASE,u.Material,u.MaterialFactoryNew())
if M:
 u.MaterialEditingLibrary.delete_all_material_expressions(M)
 M.set_editor_property('blend_mode',u.BlendMode.BLEND_ADDITIVE);M.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);M.set_editor_property('two_sided',True)
 L=u.MaterialEditingLibrary;c=L.create_material_expression(M,u.MaterialExpressionVectorParameter);c.set_editor_property('parameter_name','Color');c.set_editor_property('default_value',u.LinearColor(8,1.7,.15,1))
 a=L.create_material_expression(M,u.MaterialExpressionScalarParameter);a.set_editor_property('parameter_name','Alpha');a.set_editor_property('default_value',1)
 L.connect_material_property(c,'',u.MaterialProperty.MP_EMISSIVE_COLOR);L.connect_material_property(a,'',u.MaterialProperty.MP_OPACITY);L.recompile_material(M);ed.save_loaded_asset(M)
if (O/'animation-manifest.json').exists():
 d=json.loads((O/'animation-manifest.json').read_text());skeleton=ed.load_asset(d['skeleton'])
 for clip in d['animations']:
  opt=u.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_materials=False;opt.import_textures=False;opt.import_animations=True;opt.skeleton=skeleton;opt.automated_import_should_detect_type=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
  data=opt.anim_sequence_import_data;data.set_editor_property('convert_scene',True);data.set_editor_property('convert_scene_unit',True);data.set_editor_property('use_default_sample_rate',False);data.set_editor_property('custom_sample_rate',60)
  t=u.AssetImportTask();t.filename=str(O/clip['file']);t.destination_path=BASE;t.destination_name=clip['name'];t.automated=True;t.save=True;t.replace_existing=True;t.options=opt;t.factory=u.FbxFactory();at.import_asset_tasks([t])
  anim=ed.load_asset(BASE+'/'+clip['name']);assert isinstance(anim,u.AnimSequence),(clip['name'],list(t.imported_object_paths));anim.set_editor_property('enable_root_motion',False);ed.save_loaded_asset(anim)
  assert abs(anim.get_editor_property('sequence_length')-clip['duration_seconds'])<.025,(clip['name'],anim.get_editor_property('sequence_length'))
  report['assets'].append({'animation':anim.get_path_name(),'seconds':anim.get_editor_property('sequence_length')})
(R/'Saved/BattlePolish/import-report.json').write_text(json.dumps(report,indent=2))
