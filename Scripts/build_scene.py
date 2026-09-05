"""Assemble only the FirstDescent visual-study map, preserving other maps."""
import json
import pathlib
import unreal as u

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = '/Game/AshWell'
MAP = BASE + '/Maps/FirstDescent'
ed = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
sm_editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)

if ed.does_asset_exist(MAP):
    level.load_level(MAP)
else:
    level.new_level(MAP)
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith('AW_'):
        actors.destroy_actor(actor)

materials = {n: ed.load_asset(BASE + '/Materials/M_' + n) for n in ['Rock', 'Rust', 'Concrete', 'DarkSteel', 'Cloth', 'Leather', 'Amber']}
if not all(materials.values()):
    raise RuntimeError('Run build_materials.py before building scene')

report = {'engine': u.SystemLibrary.get_engine_version(), 'map': MAP, 'meshes': [], 'warnings': []}

def spawn(cls, name, pos=(0, 0, 0), rot=(0, 0, 0)):
    actor = actors.spawn_actor_from_class(cls, u.Vector(*pos), u.Rotator(*rot))
    actor.set_actor_label('AW_' + name)
    return actor

cache_file = ROOT / 'Saved/Automation/import-cache.json'
cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
for category in ['Geometry', 'Characters']:
    files = sorted((ROOT / 'SourceAssets' / category).glob('*.fbx'))
    if not files:
        raise RuntimeError('Missing FBX assets: ' + category)
    for file in files:
        asset_name = 'SM_' + file.stem.replace('-', '_')
        dest = BASE + '/Meshes/' + category + '/' + asset_name
        mesh = ed.load_asset(dest)
        key = str(file.relative_to(ROOT))
        if not mesh or cache.get(key) != file.stat().st_mtime_ns:
            task = u.AssetImportTask()
            task.filename = str(file)
            task.destination_path = BASE + '/Meshes/' + category
            task.destination_name = asset_name
            task.automated = True
            task.replace_existing = True
            task.save = True
            opts = u.FbxImportUI()
            opts.set_editor_property('import_mesh', True)
            opts.set_editor_property('import_as_skeletal', False)
            opts.set_editor_property('import_materials', False)
            opts.set_editor_property('import_textures', False)
            opts.set_editor_property('automated_import_should_detect_type', False)
            opts.set_editor_property('mesh_type_to_import', u.FBXImportType.FBXIT_STATIC_MESH)
            data = opts.static_mesh_import_data
            data.set_editor_property('combine_meshes', True)
            data.set_editor_property('convert_scene', True)
            data.set_editor_property('convert_scene_unit', True)
            data.set_editor_property('force_front_x_axis', False)
            data.set_editor_property('transform_vertex_to_absolute', True)
            data.set_editor_property('generate_lightmap_u_vs', False)
            data.set_editor_property('auto_generate_collision', False)
            data.set_editor_property('normal_import_method', u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
            task.options = opts
            task.factory = u.FbxFactory()
            tools.import_asset_tasks([task])
            mesh = ed.load_asset(dest)
            if not mesh:
                raise RuntimeError('FBX import failed: ' + str(file))
            cache[key] = file.stat().st_mtime_ns
        actor = spawn(u.StaticMeshActor, file.stem)
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_mobility(u.ComponentMobility.STATIC)
        # UE's FBX handedness conversion reverses source Y. Restore the agreed
        # X-forward / Y-right layout uniformly for environment and figures.
        actor.set_actor_scale3d(u.Vector(1, -1, 1))
        for i, smat in enumerate(mesh.get_editor_property('static_materials')):
            slot = str(smat.material_slot_name)
            found = next((v for k, v in materials.items() if k.lower() in slot.lower()), None)
            if found:
                comp.set_material(i, found)
            else:
                report['warnings'].append('Unmapped material slot: ' + slot)
        origin, extent = actor.get_actor_bounds(False)
        report['meshes'].append({'source': key, 'asset': dest, 'center_cm': [origin.x, origin.y, origin.z], 'extent_cm': [extent.x, extent.y, extent.z]})
cache_file.write_text(json.dumps(cache, indent=2))

camera = spawn(u.CameraActor, 'HeroCamera', (-500, 150, 210), (5.0, 0.0, 0.0))
camera.camera_component.set_editor_property('field_of_view', 65.0)
camera.camera_component.set_editor_property('aspect_ratio', 16.0/9.0)

sun = spawn(u.DirectionalLight, 'ColdBounce', (0, 0, 1000), (-48, -32, 0))
sun.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sun.light_component.set_intensity(3.0)
sun.light_component.set_light_color(u.LinearColor(0.40, 0.55, 0.69))
sun.light_component.set_editor_property('light_source_angle', 18.0)

sky = spawn(u.SkyLight, 'CavernAmbient')
sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property('source_type', u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
sky.light_component.set_editor_property('cubemap', ed.load_asset('/Engine/EngineResources/DefaultTextureCube'))
sky.light_component.set_intensity(0.32)
sky.light_component.set_light_color(u.LinearColor(0.36, 0.46, 0.58))

fog = spawn(u.ExponentialHeightFog, 'DepthFog', (0, 0, -1200))
fc = fog.component
fc.set_editor_property('fog_density', 0.018)
fc.set_editor_property('fog_height_falloff', 0.08)
fc.set_editor_property('fog_inscattering_luminance', u.LinearColor(0.065, 0.092, 0.12))
fc.set_editor_property('fog_max_opacity', 0.98)
fc.set_editor_property('enable_volumetric_fog', True)
fc.set_editor_property('volumetric_fog_distance', 24000.0)
fc.set_editor_property('volumetric_fog_scattering_distribution', 0.2)
fc.set_editor_property('volumetric_fog_emissive', u.LinearColor(0.003, 0.005, 0.008))

def point(name, pos, lumens, radius, rgb):
    a = spawn(u.PointLight, name, pos)
    lc = a.light_component
    lc.set_mobility(u.ComponentMobility.MOVABLE)
    lc.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    lc.set_intensity(lumens)
    lc.set_light_color(u.LinearColor(*rgb))
    lc.set_editor_property('attenuation_radius', radius)
    lc.set_editor_property('source_radius', 8.0)
    return a

point('PlayerLantern', (6.5, -25.1, 67.5), 780, 650, (1.0, 0.36, 0.10))
point('CompanionLantern', (695.4, -75.2, 67.5), 420, 550, (1.0, 0.39, 0.12))
point('TunnelPractical', (-190, -180, 240), 950, 650, (1.0, 0.42, 0.16))
point('DistantAmber', (8300, 1600, 1200), 7000, 1600, (1.0, 0.36, 0.07))

for name, pos, target, intensity, size in [
    ('NearColdFill', (1300, -1200, 1400), (500, 0, 0), 17000, 1500),
    ('MonumentFill', (5800, -4200, 5000), (9000, 2000, 1700), 1400000, 5000),
    ('FarRim', (14000, 2000, 4000), (8500, 2200, 1000), 1100000, 6000),
]:
    rot = u.MathLibrary.find_look_at_rotation(u.Vector(*pos), u.Vector(*target))
    a = actors.spawn_actor_from_class(u.RectLight, u.Vector(*pos), rot)
    a.set_actor_label('AW_' + name)
    lc = a.light_component
    lc.set_mobility(u.ComponentMobility.MOVABLE)
    lc.set_editor_property('intensity_units', u.LightUnits.LUMENS)
    lc.set_intensity(intensity)
    lc.set_light_color(u.LinearColor(0.36, 0.49, 0.62))
    lc.set_editor_property('source_width', float(size))
    lc.set_editor_property('source_height', float(size))
    lc.set_editor_property('attenuation_radius', 22000.0)

pp = spawn(u.PostProcessVolume, 'Grade')
pp.set_editor_property('unbound', True)
settings = pp.get_editor_property('settings')
for key, value in {
    'auto_exposure_min_brightness': 2.3,
    'auto_exposure_max_brightness': 2.3,
    'bloom_intensity': 0.28,
    'vignette_intensity': 0.22,
    'motion_blur_amount': 0.0,
    'ambient_occlusion_intensity': 0.65,
}.items():
    settings.set_editor_property('override_' + key, True)
    settings.set_editor_property(key, value)
pp.set_editor_property('settings', settings)

u.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
u.EditorLevelLibrary.editor_set_game_view(True)
level.save_current_level()
ed.save_directory(BASE, only_if_is_dirty=True, recursive=True)
report['camera_cm'] = [-500, 150, 210]
report['rendering'] = {'lumen': 'software', 'path_tracing': False, 'volumetric_fog': True, 'target_capture': '1920x1080'}
(ROOT / 'Saved/Automation/scene-report.json').write_text(json.dumps(report, indent=2))
u.log('ASHWELL: FirstDescent map assembled and saved')
