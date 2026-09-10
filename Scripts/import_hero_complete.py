from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/HeroComplete';B='/Game/AshWell/Combat/HeroComplete'
ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();L=u.MaterialEditingLibrary
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
ed.make_directory(B)
def material(name,cloth=False):
 m=ed.load_asset(B+'/'+name) or at.create_asset(name,B,u.Material,u.MaterialFactoryNew())
 L.delete_all_material_expressions(m);m.set_editor_property('used_with_skeletal_mesh',True);m.set_editor_property('used_with_clothing',cloth);m.set_editor_property('two_sided',cloth);m.set_editor_property('tangent_space_normal',True)
 def scalar(value,prop):
  n=L.create_material_expression(m,u.MaterialExpressionConstant);n.r=value;L.connect_material_property(n,'',prop)
 if cloth:
  n=L.create_material_expression(m,u.MaterialExpressionConstant3Vector);n.constant=u.LinearColor(.010,.013,.017,1);L.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR);scalar(.90,u.MaterialProperty.MP_ROUGHNESS);scalar(.12,u.MaterialProperty.MP_SPECULAR)
 else:
  for name,prop in [('BaseColor',u.MaterialProperty.MP_BASE_COLOR),('Normal',u.MaterialProperty.MP_NORMAL)]:
   n=L.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=ed.load_asset('/Game/AshWell/Combat/SwordPass/T_Traveller_'+name)
   if name=='Normal':n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
   assert n.texture;L.connect_material_property(n,'RGB',prop)
  n=L.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=ed.load_asset('/Game/AshWell/Combat/SwordPass/T_Traveller_MR');n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
  L.connect_material_property(n,'G',u.MaterialProperty.MP_ROUGHNESS);L.connect_material_property(n,'B',u.MaterialProperty.MP_METALLIC);scalar(.3,u.MaterialProperty.MP_SPECULAR)
 L.recompile_material(m);ed.save_loaded_asset(m);return m
bodymat=material('M_HeroBody');clothmat=material('M_HeroCloth',True)
skeleton=None;report={}
def imp(file,name,anim=False):
 opt=u.FbxImportUI()
 for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION if anim else u.FBXImportType.FBXIT_SKELETAL_MESH,'import_as_skeletal':True,'import_mesh':not anim,'import_animations':anim,'import_materials':False,'import_textures':False,'create_physics_asset':False}.items():opt.set_editor_property(k,v)
 if skeleton:opt.set_editor_property('skeleton',skeleton)
 d=opt.anim_sequence_import_data if anim else opt.skeletal_mesh_import_data
 d.set_editor_property('convert_scene',True);d.set_editor_property('convert_scene_unit',True)
 if anim:d.set_editor_property('use_default_sample_rate',False);d.set_editor_property('custom_sample_rate',60)
 else:d.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS);d.set_editor_property('normal_generation_method',u.FBXNormalGenerationMethod.MIKK_T_SPACE)
 t=u.AssetImportTask();t.filename=str(file);t.destination_path=B;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory();at.import_asset_tasks([t]);a=ed.load_asset(B+'/'+name);assert a,name;return a
mesh=imp(O/'SK_Hero.fbx','SK_Hero');skeleton=mesh.get_editor_property('skeleton');ed.save_loaded_asset(skeleton)
for file,name,mat in [(None,'SK_Hero',bodymat),(O/'SK_HeroCloak.fbx','SK_HeroCloak',clothmat)]:
 asset=mesh if file is None else imp(file,name)
 slots=asset.get_editor_property('materials')
 while len(slots)<2:slots.append(u.SkeletalMaterial(material_interface=mat,material_slot_name='HeroSurface'))
 for slot in slots:slot.material_interface=mat
 asset.set_editor_property('materials',slots)
 ns=asset.get_editor_property('nanite_settings');ns.set_editor_property('enabled',False);asset.set_editor_property('nanite_settings',ns)
 asset.set_editor_property('positive_bounds_extension',u.Vector(30,30,15));asset.set_editor_property('negative_bounds_extension',u.Vector(30,30,15))
 if file:report['cloth_built']=u.AshWellHeroTools.build_hero_clothing(asset)
 ed.save_loaded_asset(asset)
for file in sorted(O.glob('A_Hero_*.fbx')):
 a=imp(file,file.stem,True);report[file.stem]=a.get_editor_property('sequence_length')
ed.save_loaded_asset(skeleton);report['skeleton']=skeleton.get_path_name();(R/'Saved/HeroComplete/import.json').write_text(json.dumps(report,indent=2));u.log('HERO_COMPLETE_IMPORTED')
