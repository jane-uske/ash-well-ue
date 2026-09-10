from pathlib import Path
import unreal as u,json
R=Path(__file__).resolve().parents[1];MAP='/Game/AshWell/MountedBoss/L_MountedCourtyard'
ed=u.EditorAssetLibrary;le=u.get_editor_subsystem(u.LevelEditorSubsystem);ac=u.get_editor_subsystem(u.EditorActorSubsystem)
assert le.load_level(MAP)
for a in ac.get_all_level_actors():
 if a.get_actor_label()=="AWM_SkyBackdrop":ac.destroy_actor(a);continue
 if isinstance(a,u.DirectionalLight):a.light_component.set_intensity(8);a.light_component.set_light_color(u.LinearColor(1,.87,.67,1))
 if isinstance(a,u.SkyLight):
  c=a.light_component;c.set_editor_property('real_time_capture',False);c.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);c.set_editor_property('cubemap',ed.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap'));c.set_intensity(.9)
 if isinstance(a,u.SkyAtmosphere):ac.destroy_actor(a)
cls=ed.load_blueprint_class('/Engine/EngineSky/BP_Sky_Sphere');assert cls
sky=ac.spawn_actor_from_class(cls,u.Vector());sky.set_actor_label('AWM_SkyBackdrop');sky.set_folder_path('MountedExperiment')
sky.set_editor_property('Colors determined by sun position',False)
sky.set_editor_property('Sun height',.45)
sky.set_editor_property('Zenith color',u.LinearColor(.04,.085,.15,1))
sky.set_editor_property('Horizon color',u.LinearColor(.29,.34,.38,1))
sky.set_editor_property('Cloud color',u.LinearColor(.34,.36,.38,1))
sky.call_method('RefreshMaterial')
# The familiar engine sky gives a readable backdrop under deliberately fixed exposure.
assert le.save_current_level()
(R/'Saved/MountedBoss/lighting.json').write_text(json.dumps({'sun':8,'ambient':.9,'source':'Engine DaylightAmbientCubemap','visual_review':'pending'},indent=2))
