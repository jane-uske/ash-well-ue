import unreal as u
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
ed=u.EditorAssetLibrary
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
names={a.get_actor_label():a for a in actors.get_all_level_actors()}
# The detailed outer frame supplies the entrance shape without the original
# massive jamb hiding the column at the end of the bridge.
if 'AW_SM_MineSteelFrames' in names:actors.destroy_actor(names['AW_SM_MineSteelFrames'])
for name,intensity in {'ColdBounce':.70,'CavernAmbient':.28,'MonumentFill':110000,'FarRim':100000,'PlayerFill':1300,'NearColdFill':3500,'PlayerLantern':190,'CompanionLantern':140}.items():
    names['AW_'+name].light_component.set_intensity(intensity)
names['AW_PlayerFill'].light_component.set_light_color(u.LinearColor(.37,.45,.49))
fog=names['AW_DepthFog'].component
fog.set_editor_property('fog_density',.023)
fog.set_editor_property('fog_inscattering_luminance',u.LinearColor(.022,.034,.044))
fog.set_editor_property('volumetric_fog_emissive',u.LinearColor(.003,.006,.008))
concrete=ed.load_asset('/Game/AshWell/Materials/V2/M_Concrete')
sub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
nanite=[]
for name,a in names.items():
    if not isinstance(a,u.StaticMeshActor) or not name.startswith('AW2_'):continue
    mesh=a.static_mesh_component.static_mesh
    for i,s in enumerate(mesh.get_editor_property('static_materials')):
        if str(s.material_slot_name)=='Concrete':a.static_mesh_component.set_material(i,concrete)
    if mesh.get_path_name() in nanite:continue
    settings=sub.get_nanite_settings(mesh)
    if not settings.enabled:
        settings.enabled=True;settings.explicit_tangents=True
        sub.set_nanite_settings(mesh,settings,True)
        ed.save_loaded_asset(mesh)
    nanite.append(mesh.get_path_name())
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(root/'Saved/Automation/v2-nanite.json').write_text(json.dumps(nanite,indent=2))
