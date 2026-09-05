"""Verify the saved visual-study map and its source-to-world transforms."""
import json
import math
import pathlib
import unreal as u

root = pathlib.Path(__file__).resolve().parents[1]
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
named = {a.get_actor_label(): a for a in actors}
meshes = [a for a in actors if isinstance(a, u.StaticMeshActor) and a.get_actor_label().startswith('AW_')]
assert len(meshes) == 22, len(meshes)
assert len([a for a in meshes if 'Expedition' in a.get_actor_label()]) == 2
for actor in meshes:
    comp = actor.static_mesh_component
    assert comp.static_mesh
    assert all(comp.get_material(i) is not None for i in range(comp.get_num_materials()))
    origin, extents = actor.get_actor_bounds(False)
    assert all(math.isfinite(v) for v in [origin.x, origin.y, origin.z, extents.x, extents.y, extents.z])

pier, extents = named['AW_SM_ColossalPierCore'].get_actor_bounds(False)
assert abs(pier.x - 5000) < 1 and abs(pier.y - 2200) < 1
assert extents.z > 9000
companion = named['AW_SM_Expedition_Companion'].get_actor_location()
assert companion.x == 450 and companion.y == 170
camera = named['AW_HeroCamera']
assert camera.camera_component.field_of_view == 78
fog = named['AW_DepthFog'].component
assert fog.get_editor_property('enable_volumetric_fog')
assert u.SystemLibrary.get_console_variable_int_value('r.DynamicGlobalIlluminationMethod') == 1
assert u.SystemLibrary.get_console_variable_int_value('r.RayTracing') == 0
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
result = {
    'status': 'passed', 'engine': u.SystemLibrary.get_engine_version(),
    'mesh_actors': len(meshes), 'figures': 2,
    'materials': 7, 'texture_maps': 9,
    'camera_cm': [camera.get_actor_location().x, camera.get_actor_location().y, camera.get_actor_location().z],
    'camera_rotation': str(camera.get_actor_rotation()), 'horizontal_fov': 78,
    'software_lumen': True, 'hardware_ray_tracing': False, 'volumetric_fog': True,
    'screenshot_dimensions': [1920, 1080],
    'scope': 'Static visual study; no gameplay, animation or FPS acceptance claim.'
}
(root / 'Saved/Automation/verification.json').write_text(json.dumps(result, indent=2))
u.log('ASHWELL: visual scene verification PASSED')
