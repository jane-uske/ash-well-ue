"""Non-destructive local cloak pass; run in the inspected Blender session.

Keeps the existing rig, body, UV textures and gameplay animation assets unchanged.
Exports a derived cloak with the same bone names and weights.
"""
from pathlib import Path
import bpy, math, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'SourceAssets/TravellerPolish'
OUT.mkdir(parents=True, exist_ok=True)
source = bpy.data.objects['SK_TravellerCloak.003']
assert len(source.data.vertices) == 959, 'Inspect source before applying indexed reshape'
scene = bpy.data.scenes.new('AW_Traveller_CloakPolish')
previous_scene = bpy.context.window.scene
bpy.context.window.scene = scene
rig = source.parent.copy()
rig.data = source.parent.data.copy()
rig.animation_data_clear()
scene.collection.objects.link(rig)
rig.name = 'AW_CloakPolish_Rig'
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
cape = source.copy()
cape.data = source.data.copy()
scene.collection.objects.link(cape)
cape.name = 'SK_TravellerCloak_Polish'
cape.parent = rig
for mod in list(cape.modifiers):
    cape.modifiers.remove(mod)

# Coherent broad cloth folds, gently wrapped sides, and a clean shorter split hem.
for side, sign in enumerate((-1, 1)):
    for j in range(21):
        t = j / 20
        w = .235 + .095 * t
        for i in range(17):
            a = i / 16
            gap = .004 + .022 * max(0, (t - .55) / .45)
            y = sign * (gap + (w - gap) * a)
            fold = (.007 + .017 * t) * (math.sin(a * math.pi * 5 + .4 * t) + .22 * math.sin(a * math.pi * 9))
            x = -.157 - .095 * t + .043 * a * a + fold
            z = 1.47 - .86 * t + .011 * math.sin(a * math.pi) * t
            cape.data.vertices[side * 357 + j * 17 + i].co = (x, y, z)

# Smaller soft collar exposes the shoulders instead of a wide faceted poncho.
for j in range(5):
    t = j / 4
    for i in range(49):
        a = i / 48 * math.tau
        radius = .104 + .083 * t
        cape.data.vertices[714 + j * 49 + i].co = (
            .023 + radius * math.cos(a), radius * 1.15 * math.sin(a),
            1.465 - .078 * t * (.55 + .45 * math.cos(a)) + .007 * math.sin(a * 5) * t)
for face in cape.data.polygons:
    face.use_smooth = True
bpy.ops.object.select_all(action='DESELECT')
cape.select_set(True)
bpy.context.view_layer.objects.active = cape
sub = cape.modifiers.new('Smooth cloth folds', 'SUBSURF')
sub.levels = 1
bpy.ops.object.modifier_apply(modifier=sub.name)
solid = cape.modifiers.new('Wool hem thickness', 'SOLIDIFY')
solid.thickness = .0025
solid.offset = 0
bpy.ops.object.modifier_apply(modifier=solid.name)
arm = cape.modifiers.new('Existing cloak skin', 'ARMATURE')
arm.object = rig

occupied = bpy.data.objects.get('SK_Intro_Protagonist_Rig')
if occupied:
    occupied.name = 'AW_Preserved_OriginalRig'
name = rig.name
try:
    rig.name = 'SK_Intro_Protagonist_Rig'
    bpy.ops.object.select_all(action='DESELECT')
    cape.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(filepath=str(OUT / 'SK_TravellerCloak.fbx'),
        use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
        use_armature_deform_only=False, bake_anim=False, axis_forward='-Y', axis_up='Z',
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        primary_bone_axis='Y', secondary_bone_axis='X')
finally:
    rig.name = name
    if occupied:
        occupied.name = 'SK_Intro_Protagonist_Rig'
bpy.data.libraries.write(str(OUT / 'TravellerCloakPolish.blend'), {scene}, compress=True, fake_user=True)
result = {'vertices': len(cape.data.vertices), 'triangles': sum(len(p.vertices)-2 for p in cape.data.polygons),
          'source': source.name, 'export': str(OUT / 'SK_TravellerCloak.fbx'),
          'preserved': ['body', 'skeleton proportions', 'animations', 'weapon', 'original cloak']}
(OUT / 'manifest.json').write_text(json.dumps(result, indent=2))
bpy.context.window.scene = previous_scene
