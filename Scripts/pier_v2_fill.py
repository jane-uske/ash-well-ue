import unreal as u
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
a=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=='AW2_PierGrazingFill'),None)
pos=u.Vector(3000,6000,2000)
rot=u.MathLibrary.find_look_at_rotation(pos,u.Vector(5500,2700,800))
if not a:
    a=actors.spawn_actor_from_class(u.RectLight,pos,rot)
    a.set_actor_label('AW2_PierGrazingFill')
lc=a.light_component
lc.set_mobility(u.ComponentMobility.MOVABLE)
lc.set_editor_property('intensity_units',u.LightUnits.LUMENS)
lc.set_intensity(24000)
lc.set_light_color(u.LinearColor(.30,.40,.47))
lc.set_editor_property('source_width',800.0)
lc.set_editor_property('source_height',5000.0)
lc.set_editor_property('attenuation_radius',8500.0)
lc.set_editor_property('volumetric_scattering_intensity',.18)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
