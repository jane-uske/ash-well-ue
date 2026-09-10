from pathlib import Path
import unreal as u,json
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/SwordPass';BASE='/Game/AshWell/Combat/SwordPass';ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();ed.make_directory(BASE);report={'assets':[]}
for file in list(O.glob('SM_*.fbx'))+list(O.glob('AW_Battle_*.wav')):
 t=u.AssetImportTask();t.filename=str(file);t.destination_path=BASE;t.destination_name=file.stem;t.automated=True;t.save=True;t.replace_existing=True
 if file.suffix=='.fbx':
  opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_animations=False;opts.import_materials=True;opts.import_textures=False;opts.automated_import_should_detect_type=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
  opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.import_uniform_scale=1.;t.options=opts;t.factory=u.FbxFactory()
 at.import_asset_tasks([t]);asset=ed.load_asset(BASE+'/'+file.stem);assert asset,file;report['assets'].append(asset.get_path_name())
if (O/'animation-manifest.json').exists():
 d=json.loads((O/'animation-manifest.json').read_text());skeleton=ed.load_asset(d['skeleton'])
 for clip in d['animations']:
  opt=u.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_materials=False;opt.import_textures=False;opt.import_animations=True;opt.skeleton=skeleton;opt.automated_import_should_detect_type=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION
  data=opt.anim_sequence_import_data;data.set_editor_property('convert_scene',True);data.set_editor_property('convert_scene_unit',True);data.set_editor_property('use_default_sample_rate',False);data.set_editor_property('custom_sample_rate',60)
  t=u.AssetImportTask();t.filename=str(O/clip['file']);t.destination_path=BASE;t.destination_name=clip['name'];t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();at.import_asset_tasks([t])
  anim=ed.load_asset(BASE+'/'+clip['name']);assert isinstance(anim,u.AnimSequence),(clip['name'],list(t.imported_object_paths));anim.set_editor_property('enable_root_motion',False);ed.save_loaded_asset(anim)
  assert abs(anim.get_editor_property('sequence_length')-clip['duration_seconds'])<.025,(clip['name'],anim.get_editor_property('sequence_length'))
  report['assets'].append({'animation':anim.get_path_name(),'seconds':anim.get_editor_property('sequence_length')})
(R/'Saved/SwordPass/import-report.json').write_text(json.dumps(report,indent=2))
p=R/'Scripts/import_traveller.py'
if (O/'hero-manifest.json').exists():
 scope={'__file__':str(p)};exec(compile(p.read_text(),str(p),'exec'),scope);report['traveller']=scope['report']
report['pose_units']={}
for c in ['Idle','Walk','Run','Sprint','Guard','Slash','Heavy']:
 anim=ed.load_asset(BASE+'/A_Sword_'+c)
 report['pose_units'][c]={}
 for bone in ['SK_Intro_Protagonist_Rig','root','pelvis']:
  tr=u.AnimationLibrary.get_bone_pose_for_time(anim,bone,.3,False)
  report['pose_units'][c][bone]={'scale':[tr.scale3d.x,tr.scale3d.y,tr.scale3d.z],'translation':[tr.translation.x,tr.translation.y,tr.translation.z]}
  if bone=='SK_Intro_Protagonist_Rig':assert abs(tr.scale3d.x-100)<.01,(c,tr.scale3d)
(R/'Saved/SwordPass/pose-unit-check.json').write_text(json.dumps(report['pose_units'],indent=2))
