"""Isolated UE asset import and construction. Run in the UE editor.
Only /Game/AshWell/Combat/MountedChargeSample is written.
"""
from pathlib import Path
import json,traceback,os
import unreal as u

R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedChargeSample';B='/Game/AshWell/Combat/MountedChargeSample'
REPORT={};ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.MaterialEditingLibrary
GRAPH_ONLY=os.environ.get('ASHWELL_SAMPLE_GRAPH_ONLY')=='1'
CHARGE_ONLY=os.environ.get('ASHWELL_SAMPLE_CHARGE_ONLY')=='1'
GRAPH_ONLY=GRAPH_ONLY or CHARGE_ONLY
IK_GAITS=os.environ.get('ASHWELL_SAMPLE_IK_GAITS')=='1' or ED.does_asset_exist(B+'/BS_SampleHorse_IKSpeed')
try:
    u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    ED.make_directory(B)
    def material(label):
        name='M_Sample'+label;m=ED.load_asset(B+'/'+name) or AT.create_asset(name,B,u.Material,u.MaterialFactoryNew())
        if GRAPH_ONLY:return m
        L.delete_all_material_expressions(m);m.set_editor_property('used_with_skeletal_mesh',label in ['Knight','Horse']);m.set_editor_property('two_sided',True)
        for kind in ['BaseColor','Normal','MR']:
            file=next(O.glob('T_'+label+'_'+kind+'.*'));name='T_Sample'+label+'_'+kind
            t=u.AssetImportTask();t.filename=str(file);t.destination_path=B;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
            AT.import_asset_tasks([t]);tex=ED.load_asset(B+'/'+name);assert tex
            tex.set_editor_property('srgb',kind=='BaseColor')
            if kind=='Normal':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
            elif kind=='MR':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
            ED.save_loaded_asset(tex)
            n=L.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=tex
            if kind=='Normal':n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
            elif kind=='MR':n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
            if kind=='BaseColor':L.connect_material_property(n,'RGB',u.MaterialProperty.MP_BASE_COLOR)
            elif kind=='Normal':L.connect_material_property(n,'RGB',u.MaterialProperty.MP_NORMAL)
            else:L.connect_material_property(n,'G',u.MaterialProperty.MP_ROUGHNESS);L.connect_material_property(n,'B',u.MaterialProperty.MP_METALLIC)
        L.recompile_material(m);ED.save_loaded_asset(m);return m
    def imp(name,skeleton=None,animation=False,static=False):
        if GRAPH_ONLY and not (CHARGE_ONLY and name=='A_SampleRider_ChargeSweep') and ED.does_asset_exist(B+'/'+name):return ED.load_asset(B+'/'+name)
        opt=u.FbxImportUI()
        values={'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_ANIMATION if animation else u.FBXImportType.FBXIT_STATIC_MESH if static else u.FBXImportType.FBXIT_SKELETAL_MESH,
                'import_as_skeletal':not static,'import_mesh':not animation,'import_animations':animation,'import_materials':False,'import_textures':False,'create_physics_asset':False}
        for k,v in values.items():opt.set_editor_property(k,v)
        if skeleton:opt.skeleton=skeleton
        d=opt.anim_sequence_import_data if animation else opt.static_mesh_import_data if static else opt.skeletal_mesh_import_data
        d.set_editor_property('convert_scene',True);d.set_editor_property('convert_scene_unit',True)
        if animation:d.set_editor_property('use_default_sample_rate',False);d.set_editor_property('custom_sample_rate',60)
        t=u.AssetImportTask();t.filename=str(O/(name+'.fbx'));t.destination_path=B;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opt;t.factory=u.FbxFactory()
        AT.import_asset_tasks([t]);a=ED.load_asset(B+'/'+name);assert a,name;return a
    meshes={};skeletons={}
    for label in ['Knight','Horse','Poleaxe','Shield']:
        static=label in ['Poleaxe','Shield'];name=('SM_' if static else 'SK_')+'Sample'+label
        m=material(label);a=imp(name,static=static);meshes[label]=a
        if static:a.set_material(0,m)
        else:
            slots=[u.SkeletalMaterial(material_interface=m,material_slot_name=s.material_slot_name) for s in a.get_editor_property('materials')]
            a.set_editor_property('materials',slots);skeletons[label]=a.get_editor_property('skeleton')
            assert skeletons[label],name+' skeleton missing'
            if label=='Knight':assert u.AshWellMountedSampleTools.configure_rider_sockets(a)
            if label=='Horse':assert u.AshWellMountedSampleTools.configure_horse_sockets(a,u.Vector(-23.301632,-19.46664,57.78085),u.Vector(24.223917,-19.466648,57.78084))
            ED.save_loaded_asset(skeletons[label])
            ns=a.get_editor_property('nanite_settings');ns.set_editor_property('enabled',False);a.set_editor_property('nanite_settings',ns)
        ED.save_loaded_asset(a);REPORT[name]=a.get_path_name()
    for name in ['A_SampleRider_SeatedIdle','A_SampleRider_ChargeSweep','A_SampleHorse_Idle','A_SampleHorse_Walk','A_SampleHorse_Gallop']:
        a=imp(name,skeletons['Knight' if 'Rider' in name else 'Horse'],animation=True);REPORT[name]=a.get_editor_property('sequence_length')
    def bp(name,label,idle,blend,feet):
        f=u.AnimBlueprintFactory();f.set_editor_property('target_skeleton',skeletons[label]);f.set_editor_property('preview_skeletal_mesh',meshes[label]);f.set_editor_property('parent_class',u.AshWellMountedSampleAnimInstance)
        a=ED.load_asset(B+'/'+name) or AT.create_asset(name,B,u.AnimBlueprint,f)
        result=u.AshWellMountedSampleTools.build_animation_graph(a,ED.load_asset(B+'/'+idle),blend,feet,u.Vector(-35,-12,35),u.Vector(35,-12,35))
        REPORT[name]=result;assert 'errors=0' in result,result;ED.save_loaded_asset(a)
    blend_name='BS_SampleHorse_IKSpeed' if IK_GAITS else 'BS_SampleHorse_Speed'
    gait_prefix='HorseRetargetConnected/A_IKSampleHorse_' if IK_GAITS else 'A_SampleHorse_'
    blend=ED.load_asset(B+'/'+blend_name)
    if not blend:
        factory=u.BlendSpaceFactory1D();factory.set_editor_property('target_skeleton',skeletons['Horse'])
        blend=AT.create_asset(blend_name,B,u.BlendSpace1D,factory)
        assert u.AshWellMountedSampleTools.configure_horse_blend_space(blend,*[ED.load_asset(B+'/'+gait_prefix+n) for n in ['Idle','Walk','Gallop']])
        ED.save_loaded_asset(blend)
    bp('ABP_SampleHorse','Horse',gait_prefix+'Idle',blend,False)
    bp('ABP_SampleRider','Knight','A_SampleRider_SeatedIdle',None,True)
    montage=u.AshWellMountedSampleTools.build_charge_montage(ED.load_asset(B+'/A_SampleRider_ChargeSweep'),B+'/AM_SampleChargeSweep');assert montage
    ED.save_loaded_asset(montage);REPORT['montage']=montage.get_path_name()
    action_set=ED.load_asset(B+'/DA_MountedSampleActions')
    if not action_set:
        factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.AshWellMountedActionSet)
        action_set=AT.create_asset('DA_MountedSampleActions',B,u.AshWellMountedActionSet,factory)
    entries={str(k):v for k,v in action_set.get_editor_property('montages').items()};entries['charge']=montage;action_set.set_editor_property('montages',entries);ED.save_loaded_asset(action_set)
    REPORT['authored_actions']=[str(k) for k in entries];REPORT['passed']=True
except Exception:
    REPORT['passed']=False;REPORT['error']=traceback.format_exc();u.log_error(REPORT['error'])
finally:
    (R/'Saved/MountedChargeStandard/import.json').write_text(json.dumps(REPORT,indent=2));u.log('MOUNTED_SAMPLE_IMPORT '+json.dumps(REPORT));u.SystemLibrary.quit_editor()
