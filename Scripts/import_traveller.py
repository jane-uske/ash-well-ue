"""Import derived traveller body/cloak on existing skeleton, and explicit PBR materials."""
from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/SwordPass';BASE='/Game/AshWell/Combat/SwordPass';ed=u.EditorAssetLibrary;at=u.AssetToolsHelpers.get_asset_tools();L=u.MaterialEditingLibrary
report={'meshes':[],'textures':[]}
for f in O.glob('T_Traveller_*.png'):
 t=u.AssetImportTask();t.filename=str(f);t.destination_path=BASE;t.destination_name=f.stem;t.automated=True;t.save=True;t.replace_existing=True;at.import_asset_tasks([t]);tex=ed.load_asset(BASE+'/'+f.stem)
 if 'Normal' in f.stem:tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('srgb',False)
 elif 'MR' in f.stem:tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS);tex.set_editor_property('srgb',False)
 ed.save_loaded_asset(tex);report['textures'].append(tex.get_path_name())
def material(n):
 m=ed.load_asset(BASE+'/'+n) or at.create_asset(n,BASE,u.Material,u.MaterialFactoryNew());L.delete_all_material_expressions(m);m.set_editor_property('used_with_skeletal_mesh',True);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT);return m
def val(m,v,p):
 n=L.create_material_expression(m,u.MaterialExpressionConstant);n.r=v;L.connect_material_property(n,'',p)
def color(m,v):
 n=L.create_material_expression(m,u.MaterialExpressionConstant3Vector);n.constant=u.LinearColor(*v,1);L.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR)
body=material('M_TravellerBody');body.set_editor_property('two_sided',True);body.set_editor_property('tangent_space_normal',True)
for name,sampler,connections in [('BaseColor',u.MaterialSamplerType.SAMPLERTYPE_COLOR,[('RGB',u.MaterialProperty.MP_BASE_COLOR)]),('MR',u.MaterialSamplerType.SAMPLERTYPE_MASKS,[('G',u.MaterialProperty.MP_ROUGHNESS),('B',u.MaterialProperty.MP_METALLIC)]),('Normal',u.MaterialSamplerType.SAMPLERTYPE_NORMAL,[('RGB',u.MaterialProperty.MP_NORMAL)])]:
 n=L.create_material_expression(body,u.MaterialExpressionTextureSample);n.texture=ed.load_asset(BASE+'/T_Traveller_'+name);n.sampler_type=sampler
 for ch,prop in connections:L.connect_material_property(n,ch,prop)
# The legacy metre/root-100 skin shows corrupt tangent lighting in UE/Metal.
# Derivatives of deformed world position give stable geometric normals. Keep the
# source normal map for the future normalized-skeleton rebuild, not as a fake fix.
def geometric_normal(m):
 m.set_editor_property('tangent_space_normal',False)
 p=L.create_material_expression(m,u.MaterialExpressionWorldPosition)
 dx=L.create_material_expression(m,u.MaterialExpressionDDX);dy=L.create_material_expression(m,u.MaterialExpressionDDY)
 cross=L.create_material_expression(m,u.MaterialExpressionCrossProduct);norm=L.create_material_expression(m,u.MaterialExpressionNormalize)
 for src,out,dst,inp in [(p,'XYZ',dx,'Value'),(p,'XYZ',dy,'Value'),(dy,'',cross,'A'),(dx,'',cross,'B'),(cross,'',norm,'VectorInput')]:
  assert L.connect_material_expressions(src,out,dst,inp),inp
 assert L.connect_material_property(norm,'',u.MaterialProperty.MP_NORMAL)
geometric_normal(body)
val(body,.82,u.MaterialProperty.MP_ROUGHNESS)
L.recompile_material(body);ed.save_loaded_asset(body)
cloth=material('M_TravellerCloak');cloth.set_editor_property('two_sided',True);color(cloth,(.036,.043,.048));val(cloth,.96,u.MaterialProperty.MP_ROUGHNESS)
noise=L.create_material_expression(cloth,u.MaterialExpressionNoise);noise.set_editor_property('scale',35);mul=L.create_material_expression(cloth,u.MaterialExpressionMultiply);mul.set_editor_property('const_b',.022);L.connect_material_expressions(noise,'',mul,'A');add=L.create_material_expression(cloth,u.MaterialExpressionAdd);add.set_editor_property('const_b',.030);L.connect_material_expressions(mul,'',add,'A');L.connect_material_property(add,'',u.MaterialProperty.MP_BASE_COLOR);geometric_normal(cloth);L.recompile_material(cloth);ed.save_loaded_asset(cloth)
skeleton=ed.load_asset('/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton')
for name,mat in [('SK_Traveller',body),('SK_TravellerCloak',cloth)]:
 opts=u.FbxImportUI()
 for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH,'import_as_skeletal':True,'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False,'create_physics_asset':False,'skeleton':skeleton}.items():opts.set_editor_property(k,v)
 opts.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False)
 opts.skeletal_mesh_import_data.set_editor_property('convert_scene',True)
 opts.skeletal_mesh_import_data.set_editor_property('convert_scene_unit',True)
 opts.skeletal_mesh_import_data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
 t=u.AssetImportTask();t.filename=str(O/(name+'.fbx'));t.destination_path=BASE;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opts;t.factory=u.FbxFactory();at.import_asset_tasks([t]);mesh=ed.load_asset(BASE+'/'+name);assert isinstance(mesh,u.SkeletalMesh),name
 slots=mesh.get_editor_property('materials')
 while len(slots)<2:slots.append(u.SkeletalMaterial(material_interface=mat,material_slot_name='ImportedBody'))
 for i,slot in enumerate(slots):
  slot.set_editor_property('material_interface',mat);slots[i]=slot
 mesh.set_editor_property('materials',slots)
 # The inherited FBX root stores metres with a 100x bone scale. Raw import bounds
 # omit that root; measured CPU-skinned poses occupy roughly 180 cm, not 1.8 cm.
 mesh.set_editor_property('positive_bounds_extension',u.Vector(100,80,195))
 mesh.set_editor_property('negative_bounds_extension',u.Vector(100,80,15))
 ns=mesh.get_editor_property('nanite_settings');report[name+'_nanite_before']=ns.get_editor_property('enabled');ns.set_editor_property('enabled',False);mesh.set_editor_property('nanite_settings',ns)
 ed.save_loaded_asset(mesh);report['meshes'].append(mesh.get_path_name())
# Sword assets use explicit physical material values; FBX imports only diffuse by default.
smats={}
for name,c,metal,rough in [('Blade',(.28,.32,.35),.95,.33),('Iron',(.07,.075,.08),.85,.55),('Grip',(.05,.032,.019),0,.9),('Trim',(.18,.15,.105),.8,.6)]:
 m=material('M_Sword_'+name);color(m,c);val(m,metal,u.MaterialProperty.MP_METALLIC);val(m,rough,u.MaterialProperty.MP_ROUGHNESS);L.recompile_material(m);ed.save_loaded_asset(m);smats[name]=m
for name in ['SM_TravellerSword','SM_TravellerScabbard']:
 mesh=ed.load_asset(BASE+'/'+name)
 for i,slot in enumerate(mesh.static_materials):
  sn=str(slot.get_editor_property('material_slot_name'));key=next((k for k in smats if k in sn),'Iron');mesh.set_material(i,smats[key])
 ed.save_loaded_asset(mesh);b=mesh.get_bounds();report[name]={'center':str(b.origin),'extent':str(b.box_extent)}
(R/'Saved/SwordPass/hero-import-report.json').write_text(json.dumps(report,indent=2))
