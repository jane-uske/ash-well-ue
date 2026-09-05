import unreal as u
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
by_name = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
for name, actor in by_name.items():
    if isinstance(actor, u.StaticMeshActor) and name.startswith('AW_'):
        actor.set_actor_scale3d(u.Vector(1, -1, 1))
        if 'Expedition' in name:
            actor.set_actor_location(u.Vector(450, 0, 0), False, False)
        if 'Expedition_Companion' in name:
            # The companion moved onto the curved section of the walkway.
            actor.set_actor_location(u.Vector(450, 170, 0), False, False)

camera = by_name['AW_HeroCamera']
camera.set_actor_location(u.Vector(0, 30, 190), False, False)
camera.set_actor_rotation(u.Rotator(pitch=-5.0, yaw=7.0, roll=0.0), False)
camera.camera_component.set_editor_property('field_of_view', 78.0)

for name, intensity in {
    'ColdBounce': 1.4,
    'CavernAmbient': 0.35,
    'PlayerLantern': 230,
    'CompanionLantern': 220,
    'TunnelPractical': 100,
    'NearColdFill': 4500,
    'MonumentFill': 180000,
    'FarRim': 180000,
    'DistantAmber': 1300,
}.items():
    by_name['AW_' + name].light_component.set_intensity(intensity)
by_name['AW_PlayerLantern'].set_actor_location(u.Vector(456.5, -25.1, 67.5), False, False)
by_name['AW_CompanionLantern'].set_actor_location(u.Vector(1145.4, 94.8, 67.5), False, False)
fog = by_name['AW_DepthFog'].component
fog.set_editor_property('fog_density', 0.022)
fog.set_editor_property('fog_inscattering_luminance', u.LinearColor(0.025, 0.039, 0.052))
fog.set_editor_property('volumetric_fog_emissive', u.LinearColor(0.004, 0.008, 0.012))
u.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
u.EditorLevelLibrary.editor_set_game_view(True)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for cmd in ['r.ScreenPercentage 100', 'r.HighResScreenshotDelay 32', 'r.Lumen.ScreenProbeGather.Temporal.MaxFramesAccumulated 32']:
    u.SystemLibrary.execute_console_command(world, cmd)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()

by_name['AW_SM_MineRock_Right'].set_actor_location(u.Vector(0, 150, 0), False, False)
by_name['AW_SM_MineRock_Left'].set_actor_location(u.Vector(0, -80, 0), False, False)
fill = by_name.get('AW_PlayerFill')
if fill is None:
    pos = u.Vector(-100, -180, 400)
    rot = u.MathLibrary.find_look_at_rotation(pos, u.Vector(420, 0, 100))
    fill = actors.spawn_actor_from_class(u.RectLight, pos, rot)
    fill.set_actor_label('AW_PlayerFill')
lc = fill.light_component
lc.set_mobility(u.ComponentMobility.MOVABLE)
lc.set_editor_property('intensity_units', u.LightUnits.LUMENS)
lc.set_intensity(800)
lc.set_light_color(u.LinearColor(0.44, 0.53, 0.57))
lc.set_editor_property('source_width', 400.0)
lc.set_editor_property('source_height', 400.0)
lc.set_editor_property('attenuation_radius', 1400.0)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
