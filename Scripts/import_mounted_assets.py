"""Run once through the shared UE editor owner after background asset prep.
Writes only /Game/AshWell/Combat/MountedBoss; no existing demo asset changes.
"""
from pathlib import Path
import json
import unreal as u

R=Path(__file__).resolve().parents[1]
O=R/'SourceAssets/MountedBoss'
B='/Game/AshWell/Combat/MountedBoss'
ed=u.EditorAssetLibrary
at=u.AssetToolsHelpers.get_asset_tools()
L=u.MaterialEditingLibrary
ed.make_directory(B)
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
manifest=json.loads((O/'horse_manifest.json').read_text())
props=json.loads((O/'props_manifest.json').read_text())
report={'status':'imported, runtime verification pending','assets':{},'warnings':manifest['missing']}

def material(name,definition):
    assetname=name if name.startswith('M_') else 'M_Horse_'+name
    m=ed.load_asset(B+'/'+assetname) or at.create_asset(assetname,B,u.Material,u.MaterialFactoryNew())
    L.delete_all_material_expressions(m)
    m.set_editor_property('used_with_skeletal_mesh',True)
    c=L.create_material_expression(m,u.MaterialExpressionConstant3Vector)
    c.constant=u.LinearColor(*definition['base_color'])
    L.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
    for field,prop in [('roughness',u.MaterialProperty.MP_ROUGHNESS),('metallic',u.MaterialProperty.MP_METALLIC)]:
        n=L.create_material_expression(m,u.MaterialExpressionConstant)
        n.r=definition[field]
        L.connect_material_property(n,'',prop)
    # Keep direct PBR lighting restrained; no emissive or fake rim light.
    L.recompile_material(m);ed.save_loaded_asset(m)
    return m

materials={name:material(name,d) for name,d in {**manifest['materials'],**props['materials']}.items()}

def imp(name,kind,skeleton=None):
    opt=u.FbxImportUI()
    isanim=kind=='animation';isskin=kind=='skeletal'
    settings={
        'automated_import_should_detect_type':False,
        'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION if isanim else u.FBXImportType.FBXIT_SKELETAL_MESH if isskin else u.FBXImportType.FBXIT_STATIC_MESH,
        'import_as_skeletal':isanim or isskin,'import_mesh':not isanim,
        'import_animations':isanim,'import_materials':False,'import_textures':False,
        'create_physics_asset':False,
    }
    for k,v in settings.items():opt.set_editor_property(k,v)
    if skeleton:opt.set_editor_property('skeleton',skeleton)
    d=opt.anim_sequence_import_data if isanim else opt.skeletal_mesh_import_data if isskin else opt.static_mesh_import_data
    d.set_editor_property('convert_scene',False)
    d.set_editor_property('convert_scene_unit',False)
    d.set_editor_property('import_uniform_scale',1)
    if isanim:
        d.set_editor_property('use_default_sample_rate',False)
        d.set_editor_property('custom_sample_rate',60)
    else:
        d.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS)
        d.set_editor_property('normal_generation_method',u.FBXNormalGenerationMethod.MIKK_T_SPACE)
        if isskin:
            d.set_editor_property('update_skeleton_reference_pose',True)
        if not isskin:
            d.set_editor_property('combine_meshes',True)
            d.set_editor_property('auto_generate_collision',False)
    t=u.AssetImportTask()
    t.filename=str(O/f'{name}.fbx');t.destination_path=B;t.destination_name=name
    t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True
    t.options=opt;t.factory=u.FbxFactory();at.import_asset_tasks([t])
    a=ed.load_asset(B+'/'+name)
    assert a, name
    report['assets'][name]=a.get_path_name()
    if isanim:
        report['assets'][name]={'path':a.get_path_name(),'length':a.get_editor_property('sequence_length')}
    elif isskin:
        slots=a.get_editor_property('materials')
        for slot in slots:
            key=str(slot.get_editor_property('material_slot_name'))
            if key in materials:slot.material_interface=materials[key]
            else:u.log_warning('Mounted horse unknown material '+key)
        a.set_editor_property('materials',slots)
        ns=a.get_editor_property('nanite_settings');ns.set_editor_property('enabled',False);a.set_editor_property('nanite_settings',ns)
        a.set_editor_property('positive_bounds_extension',u.Vector(80,50,60))
        a.set_editor_property('negative_bounds_extension',u.Vector(80,50,20))
    else:
        slots=a.get_editor_property('static_materials')
        for slot in slots:
            key=str(slot.get_editor_property('material_slot_name'))
            if key in materials:slot.material_interface=materials[key]
        a.set_editor_property('static_materials',slots)
    ed.save_loaded_asset(a)
    return a

horse=imp('SK_Horse','skeletal')
skeleton=horse.get_editor_property('skeleton')
for label in manifest['clips']:imp('A_Horse_'+label,'animation',skeleton)
for name in ['SM_MountedHalberd','SM_MountedSaddle']:imp(name,'static')
ed.save_loaded_asset(skeleton)
(R/'Saved/MountedBoss').mkdir(parents=True,exist_ok=True)
(R/'Saved/MountedBoss/asset-import.json').write_text(json.dumps(report,indent=2))
u.log('MOUNTED_ASSETS_IMPORTED '+json.dumps(report))
