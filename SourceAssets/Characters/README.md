# Expedition figures for the first UE camera

Original procedural, posed static meshes authored in Blender 5.2.0 LTS. They supply human scale and the two narrative silhouettes from the concept reference. They are not rigged production characters.

- `SM_Expedition_Protagonist.fbx`: protagonist at `(0, -0.6, 0)` metres, facing +X, lantern in the right hand.
- `SM_Expedition_Companion.fbx`: companion at `(7, -0.4, 0)` metres, yaw -18 degrees, right hand signalling stop and lantern in the left hand.
- `ExpeditionFigures.blend`: both original combined meshes with materials.
- `build_expedition_figures.py`: reproducible geometry generation and export.
- `manifest.json`: dimensions, placements, lantern locations, material slots and triangle totals.
- `verify_expedition_fbx.py` and `verification.json`: successful independent FBX re-import checks.

Each FBX has one mesh at origin `(0,0,0)` with its placement baked into vertices. Units are metres. Blender source axes are +X forward, +Y right, +Z up; export uses `axis_forward='-Y', axis_up='Z'` and FBX scene units. Use UE scene-unit conversion, then verify an approximately 178 cm figure height and +X facing direction. Start with both UE actors at world origin; do not add the baked offsets twice. Localized Blender node names are handled through node type identifiers.

| Material slot | Roughness | Metallic | Intended surface |
| --- | ---: | ---: | --- |
| Cloth | 0.88 | 0 | Dark charcoal woven coat, sleeves, trousers and hood |
| DarkSteel | 0.50 | 0.83 | Helmet, shoulder plates, oxygen tanks and lantern cage |
| Rust | 0.80 | 0.40 | Oxidized edges, valves and small hardware |
| Amber | 0.25 | 0 | Lantern glass; Blender emission strength 4, bind UE emission explicitly |
| Leather | 0.73 | 0 | Gloves, boots, harness, backpack and belt pouches |

Lantern centre locations in centimetres for UE point lights, assuming the import preserves the source axes:

- Protagonist: `(6.5, -25.1, 67.5)`.
- Companion: `(695.397, -75.2005, 67.5)`.

The pair has 151,728 triangles total and retains material slots and UV layers through an FBX round trip. Coat and sleeve shapes are continuous lofted surfaces with shallow folds; plates, straps, breathing tubes and canisters are separate elements joined into each mesh. Source soles sit 1 mm above Z=0. Geometry is verified; final materials, import axes, lighting and visual acceptance still require the UE scene.
