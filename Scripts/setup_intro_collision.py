"""Add invisible simple collision to the current, parent-selected Intro map.

Executed by the project's existing editor queue. Does not load/change maps, change
engine mesh assets, start PIE, or touch anything outside this actor-name prefix.
Source route coordinates below are already the desired world X/Y in meters;
there is deliberately no FBX Y reflection when placing these native UE cubes.
"""
import bisect
import json
import math
import pathlib
import uuid
import unreal as u

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = 'AWIntroCollision_'
RUN_SUFFIX = uuid.uuid4().hex[:8]
FLOOR_TOP_M = -.025
FLOOR_HEIGHT_M = .20
FLOOR_WIDTH_M = 3.0
WALL_INNER_OFFSET_M = 1.45
WALL_THICKNESS_M = .10
WALL_HEIGHT_M = 1.10
MAX_SEGMENT_M = 1.0
FLOOR_OVERLAP_M = .08
WALL_OVERLAP_M = .14


def route(t):
    if t <= 12:
        return (-6+t, 0.0, 0.0)
    q = (t-12)/20
    return (6+18*q, 8*q*q*(3-2*q), 0.0)


def distance(a, b):
    return math.sqrt(sum((y-x)**2 for x, y in zip(a, b)))


def interpolate(a, b, alpha):
    return tuple(x+(y-x)*alpha for x, y in zip(a, b))


def resample(points, max_spacing=MAX_SEGMENT_M):
    """Preserve endpoints and redistribute stations at <= 1 m by arc length."""
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1]+distance(a, b))
    segments = int(math.ceil(cumulative[-1]/max_spacing))
    result = []
    for i in range(segments+1):
        s = cumulative[-1]*i/segments
        j = min(max(bisect.bisect_right(cumulative, s)-1, 0), len(points)-2)
        alpha = (s-cumulative[j])/(cumulative[j+1]-cumulative[j])
        result.append(interpolate(points[j], points[j+1], alpha))
    result[0], result[-1] = points[0], points[-1]
    return result


def bridge_stations():
    # Dense samples capture the smooth curve. Resample the extension separately
    # so the original visible bridge endpoint (24, 8) remains an exact station.
    curved = resample([route(4+i*.1) for i in range(281)])
    extended = resample([(24.0, 8.0, 0.0), (49.0, 23.0, 0.0)])
    return curved+extended[1:], len(curved)-1


def vec_list(v):
    return [round(float(v.x), 5), round(float(v.y), 5), round(float(v.z), 5)]


def main():
    editor = u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    cube = u.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
    assert cube is not None, 'Engine basic Cube is required; no project/engine assets were changed.'
    mesh_editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    simple_count = mesh_editor.get_simple_collision_count(cube)
    assert simple_count > 0, 'Engine Cube has no simple collision; refusing to modify the engine mesh.'
    complexity = str(mesh_editor.get_collision_complexity(cube))

    removed = 0
    for actor in list(editor.get_all_level_actors()):
        if actor.get_actor_label().startswith(PREFIX) or actor.get_name().startswith(PREFIX):
            assert editor.destroy_actor(actor), 'Could not remove owned collider: '+actor.get_actor_label()
            removed += 1

    created = []
    records = []
    counts = {'floor': 0, 'left_barrier': 0, 'right_barrier': 0, 'end_barrier': 0}

    def box(label, role, center_m, size_m, yaw, segment=None):
        pos = u.Vector(*(v*100 for v in center_m))
        actor = editor.spawn_actor_from_class(u.StaticMeshActor, pos, u.Rotator(yaw=yaw))
        assert actor is not None, 'Could not spawn '+label
        actor.set_actor_label(label)
        # Destroyed UObject names can survive until garbage collection. A run
        # suffix keeps reruns idempotent without forcing a global editor GC.
        assert actor.rename(label+'_'+RUN_SUFFIX), 'Could not prefix actor object name.'
        actor.set_editor_property('tags', [u.Name(PREFIX), u.Name(label), u.Name(PREFIX+role)])
        actor.set_folder_path('AshWell/IntroCollision')
        component = actor.static_mesh_component
        component.set_static_mesh(cube)
        actor.set_actor_scale3d(u.Vector(*size_m))  # BasicShapes/Cube is exactly 100 cm per side.
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_object_type(u.CollisionChannel.ECC_WORLD_STATIC)
        # FBodyInstance::SetObjectType invalidates the profile even when the
        # channel is unchanged. Apply the canonical profile LAST and verify it.
        component.set_collision_profile_name('BlockAll')
        component.set_editor_property('generate_overlap_events', False)
        component.set_simulate_physics(False)
        actor.set_actor_enable_collision(True)
        # Render visibility and physical collision are independent in UE.
        actor.set_actor_hidden_in_game(True)
        component.set_hidden_in_game(True)
        component.set_visibility(False)
        component.set_editor_property('cast_shadow', False)
        component.set_editor_property('cast_hidden_shadow', False)
        component.set_editor_property('affect_distance_field_lighting', False)
        component.set_editor_property('affect_dynamic_indirect_lighting', False)
        component.set_editor_property('visible_in_ray_tracing', False)
        component.set_editor_property('render_in_main_pass', False)
        component.set_editor_property('render_in_depth_pass', False)

        origin, extent = actor.get_actor_bounds(False)
        actual = {
            'profile': str(component.get_collision_profile_name()),
            'enabled': str(component.get_collision_enabled()),
            'object_type': str(component.get_collision_object_type()),
            'pawn_response': str(component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
            'actor_collision_enabled': actor.get_actor_enable_collision(),
            'actor_hidden_in_game': bool(actor.get_editor_property('hidden')),
            'component_hidden_in_game': bool(component.get_editor_property('hidden_in_game')),
            'component_visible': bool(component.get_editor_property('visible')),
            'cast_shadow': bool(component.get_editor_property('cast_shadow')),
            'render_in_main_pass': bool(component.get_editor_property('render_in_main_pass')),
            'render_in_depth_pass': bool(component.get_editor_property('render_in_depth_pass')),
            'mobility': str(component.get_editor_property('mobility')),
        }
        assert actual['profile'] == 'BlockAll', actual
        assert component.get_collision_enabled() == u.CollisionEnabled.QUERY_AND_PHYSICS, actual
        assert component.get_collision_object_type() == u.CollisionChannel.ECC_WORLD_STATIC, actual
        assert component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN) == u.CollisionResponseType.ECR_BLOCK, actual
        assert actual['actor_collision_enabled'] and actual['actor_hidden_in_game'], actual
        assert not actual['component_visible'] and not actual['cast_shadow'], actual
        assert not actual['render_in_main_pass'] and not actual['render_in_depth_pass'], actual
        assert component.get_editor_property('mobility') == u.ComponentMobility.STATIC, actual
        records.append({
            'label': label, 'object_name': actor.get_name(), 'role': role, 'segment': segment,
            'center_cm': vec_list(actor.get_actor_location()),
            'size_cm': [round(v*100, 5) for v in size_m], 'yaw_degrees': round(yaw, 7),
            'bounds_origin_cm': vec_list(origin), 'bounds_extent_cm': vec_list(extent),
            'collision_and_visibility': actual,
        })
        created.append(actor)
        counts[role] += 1

    stations, original_segments = bridge_stations()
    assert stations[0] == (-2.0, 0.0, 0.0)
    assert stations[-1] == (49.0, 23.0, 0.0)
    segments = []
    for i, (a, b) in enumerate(zip(stations, stations[1:])):
        length = distance(a, b)
        assert 0 < length <= MAX_SEGMENT_M+1e-6
        tangent = ((b[0]-a[0])/length, (b[1]-a[1])/length)
        side = (-tangent[1], tangent[0])
        yaw = math.degrees(math.atan2(tangent[1], tangent[0]))
        middle = interpolate(a, b, .5)
        box(PREFIX+f'Floor_{i:03d}', 'floor',
            (middle[0], middle[1], FLOOR_TOP_M-FLOOR_HEIGHT_M/2),
            (length+FLOOR_OVERLAP_M, FLOOR_WIDTH_M, FLOOR_HEIGHT_M), yaw, i)
        for sign, role in [(-1, 'left_barrier'), (1, 'right_barrier')]:
            offset = sign*(WALL_INNER_OFFSET_M+WALL_THICKNESS_M/2)
            box(PREFIX+f'{role.title().replace("_", "")}_{i:03d}', role,
                (middle[0]+side[0]*offset, middle[1]+side[1]*offset,
                 FLOOR_TOP_M+WALL_HEIGHT_M/2),
                (length+WALL_OVERLAP_M, WALL_THICKNESS_M, WALL_HEIGHT_M), yaw, i)
        segments.append({'index': i, 'start_m': list(a), 'end_m': list(b),
                         'centerline_length_m': round(length, 8),
                         'part': 'original_bridge' if i < original_segments else 'straight_extension'})

    for label, point, neighbor, outward in [
            ('Start', stations[0], stations[1], -1),
            ('End', stations[-1], stations[-2], 1)]:
        if outward == -1:
            tx, ty = neighbor[0]-point[0], neighbor[1]-point[1]
        else:
            tx, ty = point[0]-neighbor[0], point[1]-neighbor[1]
        length = math.hypot(tx, ty)
        tx, ty = tx/length, ty/length
        center = (point[0]+outward*tx*WALL_THICKNESS_M/2,
                  point[1]+outward*ty*WALL_THICKNESS_M/2,
                  FLOOR_TOP_M+WALL_HEIGHT_M/2)
        box(PREFIX+label+'Barrier', 'end_barrier', center,
            (WALL_THICKNESS_M, 2*(WALL_INNER_OFFSET_M+WALL_THICKNESS_M), WALL_HEIGHT_M),
            math.degrees(math.atan2(ty, tx)))

    bounds_min = [min(r['bounds_origin_cm'][j]-r['bounds_extent_cm'][j] for r in records) for j in range(3)]
    bounds_max = [max(r['bounds_origin_cm'][j]+r['bounds_extent_cm'][j] for r in records) for j in range(3)]
    report = {
        'status': 'passed', 'engine': u.SystemLibrary.get_engine_version(), 'world': world.get_path_name(),
        'ownership_prefix': PREFIX, 'removed_previous_owned_actors': removed,
        'created_actors': len(created), 'counts': counts,
        'source_mesh': cube.get_path_name(), 'source_simple_collision_count': simple_count,
        'source_collision_complexity': complexity,
        'floor_top_cm': FLOOR_TOP_M*100, 'floor_height_cm': FLOOR_HEIGHT_M*100,
        'floor_width_cm': FLOOR_WIDTH_M*100, 'barrier_inner_offset_cm': WALL_INNER_OFFSET_M*100,
        'barrier_thickness_cm': WALL_THICKNESS_M*100, 'barrier_height_cm': WALL_HEIGHT_M*100,
        'expected_character_capsule': {'radius_cm': 28, 'half_height_cm': 88},
        'route_length_m': round(sum(s['centerline_length_m'] for s in segments), 7),
        'route_stations_m': [list(p) for p in stations], 'segments': segments,
        'world_bounds_cm': {'min': bounds_min, 'max': bounds_max},
        'actors': records,
        'scope': 'Static native simple-collision cubes; no render geometry or engine assets modified. Actual character movement still requires parent PIE verification.',
    }
    assert counts['floor'] == len(stations)-1
    assert counts['left_barrier'] == counts['right_barrier'] == counts['floor']
    assert counts['end_barrier'] == 2
    assert levels.save_current_level(), 'Could not save current Intro level.'
    path = ROOT/'Saved'/'Automation'/'intro-collision-report.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+'\n')
    u.log(f'ASHWELL INTRO: {len(created)} hidden BlockAll simple-collision actors saved; report: {path}')


if __name__ == '__main__':
    main()
