"""UE editor: assemble the approved reference field from real imported assets."""
import unreal as u
import json,math,random,traceback,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'SourceAssets/MountedReferenceProduction';B='/Game/AshWell/MountedBoss/ReferenceProduction'
ED=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
AC=u.get_editor_subsystem(u.EditorActorSubsystem);LE=u.get_editor_subsystem(u.LevelEditorSubsystem);SS=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
report={'assets':{},'instances':{}};cache={}
REUSE=os.environ.get('ASHWELL_REFERENCE_REUSE_ASSETS')=='1'

import runpy
ground=runpy.run_path(str(R/'Scripts/mounted_reference_layout.py'))['ground']

def tex(file,name,normal=False,linear=False):
    if name in cache:return cache[name]
    if REUSE and ED.does_asset_exist(B+'/'+name):cache[name]=ED.load_asset(B+'/'+name);return cache[name]
    task=u.AssetImportTask();task.filename=str(file);task.destination_path=B;task.destination_name=name
    task.automated=True;task.save=True;task.replace_existing=True;AT.import_asset_tasks([task])
    a=ED.load_asset(B+'/'+name);assert a,name
    a.set_editor_property('srgb',not (normal or linear))
    if normal:
        a.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
        a.set_editor_property('flip_green_channel',True)
    elif linear:a.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
    ED.save_loaded_asset(a);cache[name]=a;return a

def material(name,base,normal=None,rough=None,alpha=None,tint=(1,1,1),foliage=False,wind=0,uv_scale=1.):
    if REUSE and os.environ.get('ASHWELL_REFERENCE_REBUILD_MATERIALS')!='1' and ED.does_asset_exist(B+'/'+name):return ED.load_asset(B+'/'+name)
    m=ED.load_asset(B+'/'+name) or AT.create_asset(name,B,u.Material,u.MaterialFactoryNew())
    ML.delete_all_material_expressions(m)
    m.set_editor_property('two_sided',bool(alpha or foliage))
    m.set_editor_property('used_with_instanced_static_meshes',True)
    m.set_editor_property('used_with_nanite',True)
    if alpha:m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('opacity_mask_clip_value',.38)
    if foliage:m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    def constant(value):
        n=ML.create_material_expression(m,u.MaterialExpressionConstant);n.r=value;return n
    def sample(texture,normal_map=False,mask=False):
        n=ML.create_material_expression(m,u.MaterialExpressionTextureSample);n.texture=texture
        if uv_scale!=1.:
            uv=ML.create_material_expression(m,u.MaterialExpressionTextureCoordinate);uv.set_editor_property('u_tiling',uv_scale);uv.set_editor_property('v_tiling',uv_scale);ML.connect_material_expressions(uv,'',n,'UVs')
        if normal_map:n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
        elif mask:n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
        return n
    color=sample(base);mul=ML.create_material_expression(m,u.MaterialExpressionMultiply)
    tint_node=ML.create_material_expression(m,u.MaterialExpressionConstant3Vector);tint_node.constant=u.LinearColor(*tint,1)
    ML.connect_material_expressions(color,'RGB',mul,'A');ML.connect_material_expressions(tint_node,'',mul,'B')
    ML.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
    if foliage:
        sub=ML.create_material_expression(m,u.MaterialExpressionMultiply);sub.set_editor_property('const_b',.45)
        ML.connect_material_expressions(mul,'',sub,'A');ML.connect_material_property(sub,'',u.MaterialProperty.MP_SUBSURFACE_COLOR)
    if normal:ML.connect_material_property(sample(normal,True),'RGB',u.MaterialProperty.MP_NORMAL)
    if rough:ML.connect_material_property(sample(rough,mask=True),'R',u.MaterialProperty.MP_ROUGHNESS)
    else:ML.connect_material_property(constant(.86),'',u.MaterialProperty.MP_ROUGHNESS)
    ML.connect_material_property(constant(.22),'',u.MaterialProperty.MP_SPECULAR)
    if alpha:ML.connect_material_property(sample(alpha,mask=True),'R',u.MaterialProperty.MP_OPACITY_MASK)
    if wind:
        f=ML.create_material_expression(m,u.MaterialExpressionMaterialFunctionCall)
        f.set_material_function(ED.load_asset('/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind'))
        names=list(ML.get_material_expression_input_names(f));report.setdefault('wind_inputs',names)
        vertex=ML.create_material_expression(m,u.MaterialExpressionVertexColor)
        for n in names:
            if 'Intensity' in n:ML.connect_material_expressions(constant(wind),'',f,n)
            elif 'Weight' in n:ML.connect_material_expressions(vertex,'A',f,n)
            elif 'Speed' in n:ML.connect_material_expressions(constant(.65),'',f,n)
            elif 'AdditionalWPO' in n:
                zero=ML.create_material_expression(m,u.MaterialExpressionConstant3Vector);zero.constant=u.LinearColor(0,0,0,0)
                ML.connect_material_expressions(zero,'',f,n)
        ML.connect_material_property(f,'',u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    ML.recompile_material(m);ED.save_loaded_asset(m);return m

def mesh(name,materials,solid=True,nanite=True):
    reimport_foliage=os.environ.get('ASHWELL_REFERENCE_REIMPORT_FOLIAGE')=='1' and any(n in name for n in ['Grass','Broadleaf','BareTree'])
    if REUSE and not reimport_foliage and name!='SM_ReferenceField' and ED.does_asset_exist(B+'/'+name):
        a=ED.load_asset(B+'/'+name)
        if name=='SM_ReferenceField':
            settings=SS.get_nanite_settings(a);settings.fallback_relative_error=0.;SS.set_nanite_settings(a,settings,True);ED.save_loaded_asset(a)
        report['assets'][name]={'path':a.get_path_name(),'reused_import':True};return a
    opt=u.FbxImportUI()
    for k,v in {'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_STATIC_MESH,
        'import_as_skeletal':False,'import_mesh':True,'import_animations':False,'import_materials':False,'import_textures':False}.items():opt.set_editor_property(k,v)
    d=opt.static_mesh_import_data
    for k,v in {'convert_scene':True,'convert_scene_unit':True,'combine_meshes':True,'auto_generate_collision':False,'vertex_color_import_option':u.VertexColorImportOption.REPLACE}.items():d.set_editor_property(k,v)
    task=u.AssetImportTask();task.filename=str(O/(name+'.fbx'));task.destination_path=B;task.destination_name=name
    task.automated=True;task.save=True;task.replace_existing=True;task.replace_existing_settings=True;task.options=opt;task.factory=u.FbxFactory();AT.import_asset_tasks([task])
    a=ED.load_asset(B+'/'+name);assert a,name
    slots=a.get_editor_property('static_materials')
    for i,slot in enumerate(slots):
        chosen=materials.get(str(slot.material_slot_name)) if isinstance(materials,dict) else materials
        assert chosen,(name,str(slot.material_slot_name));a.set_material(i,chosen)
    body=a.get_editor_property('body_setup');assert body,name+' BodySetup'
    body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if solid else u.CollisionTraceFlag.CTF_USE_DEFAULT)
    if nanite:
        settings=SS.get_nanite_settings(a);settings.enabled=True;settings.explicit_tangents=True
        if name=='SM_ReferenceField':
            settings.generate_fallback=u.NaniteGenerateFallback.ENABLED;settings.fallback_target=u.NaniteFallbackTarget.PERCENT_TRIANGLES;settings.fallback_percent_triangles=1.;settings.fallback_relative_error=0.
        SS.set_nanite_settings(a,settings,True)
    ED.save_loaded_asset(a);report['assets'][name]={'path':a.get_path_name(),'nanite':nanite,'collision':solid,'materials':len(slots)};return a

def actor(cls,name,position=(0,0,0),rotation=None):
    a=AC.spawn_actor_from_class(cls,u.Vector(*position),rotation or u.Rotator());a.set_actor_label('AWM_Reference_'+name);a.set_folder_path('MountedReferenceProduction');return a

def prop(name,asset,x,y,scale=1,yaw=0,buried=0,solid=True):
    a=actor(u.StaticMeshActor,name,(x,y,ground(x,y)+buried),u.Rotator(yaw=yaw))
    a.static_mesh_component.set_static_mesh(asset);a.set_actor_scale3d(u.Vector(scale,scale,scale))
    a.static_mesh_component.set_collision_profile_name('BlockAll' if solid else 'NoCollision');return a

try:
    ED.make_directory(B);u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
    ledger=json.loads((R/'Docs/Implementation/MountedBoss/ChargeSample/meshy-reference-budget.json').read_text())
    props={}
    for key,label in [('wall','RuinWall'),('rock','FlatRock'),('stake','RoadsideStake'),('castle','DistantFortress')]:
        if key not in ledger['assets']:continue
        folder=R/ledger['assets'][key]['project_dir']
        m=material('M_Reference'+label,tex(folder/'texture_0_base_color.png','T_Reference'+label+'Color'),
            tex(folder/'texture_0_normal.png','T_Reference'+label+'Normal',normal=True),
            tex(folder/'texture_0_roughness.png','T_Reference'+label+'Roughness',linear=True))
        props[key]=mesh('SM_Reference'+label,m,solid=key in ('wall','rock'))
    grass_dir=O/'Vegetation/grass_medium_01/textures'
    gm=material('M_ReferenceGrass',tex(grass_dir/'grass_medium_01_diff_2k.jpg','T_ReferenceGrassColor'),
        tex(grass_dir/'grass_medium_01_nor_gl_2k.exr','T_ReferenceGrassNormal',normal=True),
        tex(grass_dir/'grass_medium_01_rough_2k.exr','T_ReferenceGrassRoughness',linear=True),
        tex(grass_dir/'grass_medium_01_alpha_2k.png','T_ReferenceGrassAlpha',linear=True),tint=(.92,.9,.70),foliage=True,wind=.06)
    grasses=[mesh('SM_ReferenceGrass'+name,gm,solid=False,nanite=False) for name in ['Tall','Mid','Dense']]
    tree_dir=O/'Vegetation/jacaranda_tree/textures';tree_materials={}
    for part in ['trunk','branches','leaves']:
        def file(kind):return next(tree_dir.glob('jacaranda_tree_'+part+'_'+kind+'_2k.*'))
        leaf=part=='leaves'
        m=material('M_ReferenceTree'+part,tex(file('diff'),'T_ReferenceTree'+part+'Color'),
            tex(file('nor_gl'),'T_ReferenceTree'+part+'Normal',normal=True),
            tex(file('rough'),'T_ReferenceTree'+part+'Roughness',linear=True),
            tex(file('alpha'),'T_ReferenceTreeLeafAlpha',linear=True) if leaf else None,
            tint=(1.35,.83,.35) if leaf else (1,1,1),foliage=leaf,wind=.015 if leaf else 0)
        tree_materials['jacaranda_tree_'+part]=m
    tree=mesh('SM_ReferenceBroadleaf',tree_materials,solid=False)
    bare=mesh('SM_ReferenceBareTree',tree_materials,solid=False)
    ground_dir=O/'Ground'
    earth=material('M_ReferenceEarth',tex(next(ground_dir.glob('aerial*diff*')),'T_ReferenceMeadowColor'),
        tex(next(ground_dir.glob('aerial*nor_gl*')),'T_ReferenceMeadowNormal',normal=True),
        tex(next(ground_dir.glob('aerial*rough*')),'T_ReferenceMeadowRoughness',linear=True),tint=(.12,.15,.09),uv_scale=400/1500)
    field=mesh('SM_ReferenceField',earth)
    assert LE.load_level('/Game/AshWell/MountedBoss/L_MountedCourtyard')
    # Only the existing mounted set dressing is replaced; other maps and assets survive.
    for a in list(AC.get_all_level_actors()):
        if a.get_actor_label().startswith('AWM_'):AC.destroy_actor(a)
    field_actor=actor(u.StaticMeshActor,'ContinuousField');field_actor.static_mesh_component.set_static_mesh(field);field_actor.static_mesh_component.set_collision_profile_name('BlockAll')
    # A single thin 360 m sheet creates metre-sized software distance-field voxels.
    # Keep actual triangle collision/shadows; exclude this sheet from coarse SDF occlusion.
    field_actor.static_mesh_component.set_editor_property('affect_distance_field_lighting',False)
    for i,(x,y,s,yaw) in enumerate([(-350,-460,1.2,22),(500,-650,1.05,-10),(1050,-1000,1.55,9),(-950,460,.85,41),(400,850,1.2,10),(1700,1020,1.5,-24),(2500,-1650,1.9,18)]):
        prop('Rock'+str(i),props['rock'],x,y,s,yaw,-14)
    for i,y in enumerate([1180,1740,2300]):prop('Wall'+str(i),props['wall'],2260,y,1.45,90,-20)
    for i,(x,y) in enumerate([(-400,-800),(180,-1060),(760,-1320),(1340,-1580),(1940,-1840),(2580,-2200)]):
        prop('RoadsideStake'+str(i),props['stake'],x,y,.85+.07*(i%3),8*i,-16,False)
    rng=random.Random(91226)
    for i,(x,y,s) in enumerate([(1500,-3100,.5),(3200,-1600,.55),(3400,2200,.50),(900,3600,.55),(-1600,-3300,.45),(-2800,1900,.5),(-1000,4400,.48),(4400,-3900,.60),(6100,2800,.65),(-4500,-3600,.55)]):
        prop('Broadleaf'+str(i),tree,x,y,s,rng.uniform(0,360),-3,False)
    for i,(x,y) in enumerate([(1200,-2500),(2600,700),(3200,1600),(-2400,-1500),(-2500,3400),(4800,3200)]):
        prop('BareTree'+str(i),bare,x,y,.28+.04*(i%3),rng.uniform(0,360),-3,False)
    # Distant geometry is a silhouette interpretation: the source does not reveal its back.
    if 'castle' in props:
        # The wide model spans several terrain elevations. Sink the foundation
        # below the near hillside; anchoring at only its centre left it floating.
        prop('DistantFortress',props['castle'],-9000,-4500,1.0,-30,60-ground(-9000,-4500),False)
    for i in range(24):
        x=rng.uniform(-7500,-3100);y=rng.choice([-1,1])*rng.uniform(1900,4300)
        prop('BackgroundGrove'+str(i),tree,x,y,rng.uniform(.48,.78),rng.uniform(0,360),-3,False)
    groups=[[],[],[]]
    for x in range(-3500,4000,32):
        for y in range(-3000,3400,32):
            px=x+rng.uniform(-20,20);py=y+rng.uniform(-20,20)
            # A thin worn route keeps hoof contact and telegraphs legible.
            if abs(py-100*math.sin(px/850))<105 and rng.random()<.65:continue
            if rng.random()<.13:continue
            pick=rng.random();kind=2 if pick<.42 else (0 if pick<.90 else 1)
            scale=rng.uniform(1.25,2.05)
            groups[kind].append(u.Transform(u.Vector(px,py,ground(px,py)-1),u.Rotator(yaw=rng.uniform(0,360)),u.Vector(scale,scale,scale)))
    for i in range(1600):
        x=rng.uniform(-3400,3900);y=rng.uniform(-2900,3300)
        if abs(y)<120:continue
        scale=rng.uniform(1.4,2.1);groups[2].append(u.Transform(u.Vector(x,y,ground(x,y)-1),u.Rotator(yaw=rng.uniform(0,360)),u.Vector(scale,scale,scale)))
    for i,instances in enumerate(groups):
        owner=actor(u.Actor,'GrassInstances'+str(i))
        count=u.AshWellReferenceEnvironmentTools.add_foliage_instances(owner,grasses[i],instances,4200,False)
        assert count==len(instances);report['instances'][str(i)]=count
    actor(u.PlayerStart,'PlayerStart',(-2050,0,ground(-2050,0)+100))
    sun=actor(u.DirectionalLight,'Sun',(0,0,1500),u.Rotator(pitch=-34,yaw=-42));light=sun.light_component
    light.set_mobility(u.ComponentMobility.MOVABLE);light.set_intensity(1.8);light.set_light_color(u.LinearColor(1,.91,.78,1));light.set_editor_property('atmosphere_sun_light',True);light.set_editor_property('light_source_angle',12.0)
    actor(u.SkyAtmosphere,'Atmosphere',(0,0,-100))
    cloud=actor(u.VolumetricCloud,'CloudLayer');cloud_component=cloud.get_component_by_class(u.VolumetricCloudComponent)
    cloud_component.set_material(ED.load_asset('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst'))
    sky=actor(u.SkyLight,'Ambient',(0,0,1200));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_intensity(1.25);sky.light_component.set_editor_property('real_time_capture',False);sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
    hdri_path=B+'/T_ReferenceOvercastSky'
    if not ED.does_asset_exist(hdri_path):
        task=u.AssetImportTask();task.filename=str(O/'Lighting/overcast_soil_puresky_2k.hdr');task.destination_path=B;task.destination_name='T_ReferenceOvercastSky';task.automated=True;task.save=True;AT.import_asset_tasks([task])
    hdri=ED.load_asset(hdri_path);assert isinstance(hdri,u.TextureCube),hdri
    sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_cubemap(hdri)
    fog=actor(u.ExponentialHeightFog,'Haze',(0,0,-120));fog.component.set_fog_density(.022);fog.component.set_fog_height_falloff(.12);fog.component.set_start_distance(1700);fog.component.set_fog_inscattering_color(u.LinearColor(.42,.42,.31,1));fog.component.set_fog_max_opacity(.85)
    post=actor(u.PostProcessVolume,'Exposure');post.set_editor_property('unbound',True);settings=post.get_editor_property('settings')
    for key,value in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0.0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_bloom_intensity',True),('bloom_intensity',.1),('override_vignette_intensity',True),('vignette_intensity',.08),('override_motion_blur_amount',True),('motion_blur_amount',0.0)]:settings.set_editor_property(key,value)
    post.set_editor_property('settings',settings)
    assert LE.save_current_level();u.AshWellReferenceEnvironmentTools.finish_asset_compilation();report['passed']=True
except Exception:
    report['passed']=False;report['error']=traceback.format_exc();u.log_error(report['error'])
finally:
    (R/'Saved/MountedReferenceProduction/environment-import.json').write_text(json.dumps(report,indent=2));u.log('REFERENCE_ENVIRONMENT '+json.dumps(report))
    # A startup script runs before the first editor UI frame is complete. Allow
    # Slate to finish initialization before requesting its ordinary shutdown.
    if __import__('os').environ.get('ASHWELL_REFERENCE_CHAINED')!='1':
        u.EditorPythonScripting.set_keep_python_script_alive(True)
        _finished=time.monotonic()
        def _finish_editor(delta):
            if time.monotonic()-_finished>3:
                u.unregister_slate_post_tick_callback(_finish_handle)
                u.SystemLibrary.quit_editor()
        _finish_handle=u.register_slate_post_tick_callback(_finish_editor)
