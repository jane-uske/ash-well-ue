from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/JumpPolish';B='/Game/AshWell/Combat/JumpPolish'
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();ed.make_directory(B);report={}
for f in sorted(O.glob('A_Hero_Jump*.fbx')):
 opt=u.FbxImportUI()
 for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION,'import_as_skeletal':True,'import_mesh':False,'import_animations':True,'import_materials':False,'import_textures':False,'skeleton':ed.load_asset('/Game/AshWell/Combat/HeroComplete/SK_Hero_Skeleton')}.items():opt.set_editor_property(k,v)
 d=opt.anim_sequence_import_data;d.set_editor_property('convert_scene',True);d.set_editor_property('convert_scene_unit',True);d.set_editor_property('use_default_sample_rate',False);d.set_editor_property('custom_sample_rate',60)
 t=u.AssetImportTask();t.filename=str(f);t.destination_path=B;t.destination_name=f.stem;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();at.import_asset_tasks([t]);a=ed.load_asset(B+'/'+f.stem);assert a;report[f.stem]=a.get_editor_property('sequence_length')
(R/'Saved/JumpPolish/import.json').write_text(json.dumps(report,indent=2));u.log('HERO_JUMP_PHASES_IMPORTED')
