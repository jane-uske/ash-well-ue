import json
from pathlib import Path
import unreal as u
root=Path(__file__).resolve().parents[1]
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in actors.get_all_level_actors():
    if a.get_actor_label().startswith('AW2_Practical_'):actors.destroy_actor(a)
def point(name,pos,lumens,radius):
    a=actors.spawn_actor_from_class(u.PointLight,u.Vector(*(v*100 for v in pos)))
    a.set_actor_label('AW2_Practical_'+name)
    lc=a.light_component;lc.set_mobility(u.ComponentMobility.MOVABLE)
    lc.set_editor_property('intensity_units',u.LightUnits.LUMENS)
    lc.set_intensity(lumens);lc.set_light_color(u.LinearColor(1,.43,.14))
    lc.set_editor_property('attenuation_radius',radius*100)
    lc.set_editor_property('source_radius',8.0)
    lc.set_editor_property('volumetric_scattering_intensity',.2)
    return a
for a in json.loads((root/'SourceAssets/ArchitectureV2/warm_room_light_anchors.json').read_text())['anchors']:
    point(a['name'],a['position_m'],a['suggested_lumens'],a['suggested_radius_m'])
for i,(p,l,r) in enumerate([((48.1,23,1.8),350,4),((49,23,-21),500,5),((58,32,-31),360,4)]):point('Pier_'+str(i),p,l,r)
d=json.loads((root/'SourceAssets/SurfaceV2/DeepCrossing/manifest.json').read_text())
for i,a in enumerate(d['light_anchors']):
    p=a.get('source_m')
    if p is None:raise RuntimeError(str(a))
    point('LowerBridge_'+str(i),p,350,4.0)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
