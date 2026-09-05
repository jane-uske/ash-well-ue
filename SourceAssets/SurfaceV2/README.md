# Surface V2

This folder contains original bridge-surface geometry plus three free CC0
texture sets for the second Ash Well visual iteration. Nothing here imports
into or modifies a running Unreal scene automatically.

## Geometry

`surface_manifest.json` is the geometry/import manifest. Its three FBX files
contain 131,200 triangles total:

| File | Purpose |
| --- | --- |
| `SM_SurfaceV2_BrokenStoneDeck.fbx` | 432 irregular slabs, chipped rims, occasional split stones, shallow worn relief |
| `SM_SurfaceV2_MortarAndDebris.fbx` | Recessed mortar and 296 small chips, mainly beside the gutters |
| `SM_SurfaceV2_SteelRepairs.fbx` | Three narrow repair straps and small fasteners |

Replace only the original `SM_WalkwayDeck` actor; keep its original edge beams,
railings and under-truss. The centreline uses the exact old `route(t)` for
`t=4..32`, from x=-2 m to x=24 m. Width is 2.94 m inside the original 3 m
structural edges. All three mesh origins and transforms are zero/identity.
Coordinates are metres, +X forward, +Y right, +Z up. The parent scene importer
handles the existing UE Y-mirror convention; it is not baked into these meshes.

All files have material slots in this order: `WetStone`, `Debris`, `DarkSteel`.
UV0 is world-scaled at one UV unit per metre, so the supplied 2 m stone/steel
textures use a TextureCoordinate multiplier of 0.5. Vertex RGB stores modest
per-slab variation; vertex alpha optionally drives wetness. Import vertex
colors using Replace if using those channels.

The slab tops remain below z=0, generally within three centimetres of it. The
two standing areas are capped at z=-0.005 m and loose debris avoids the boots.
Do not raise the figures. The substrate fills cracks at about z=-0.038 m.

## Textures and license

Powered by Poly Haven. `texture_manifest.json` records each official download
URL, license, author, physical size, file size, MD5 and SHA-256. The 11 original
2K texture maps total 94,791,509 bytes. No paid assets were purchased.

| Material key | Source | Physical tile |
| --- | --- | --- |
| `WetStone` | [Slate Floor 03](https://polyhaven.com/a/slate_floor_03) | 2 × 2 m |
| `DarkCloth` | [Denim Fabric 06](https://polyhaven.com/a/denim_fabric_06) | approximately 0.254 × 0.254 m |
| `OldSteel` | [Rusty Metal 04](https://polyhaven.com/a/rusty_metal_04) | 2 × 2 m |

All maps are [CC0-1.0 under Poly Haven's official asset license](https://polyhaven.com/license).
Only texture assets are included, not website preview renders or logos.
The cloth is dark, worn denim/twill rather than a literal canvas scan; it
provides a dense coarse-fibre surface for the current expedition clothing.

Base color uses sRGB; roughness, displacement, packed ARM and normals do not.
Normals are DirectX: **do not flip the green channel in Unreal**. OldSteel ARM
packs ambient occlusion in R, roughness in G and metallic in B. Slate also
includes displacement, but no runtime displacement is required by the meshes.

The original slate diffuse is brown. For the cool damp reference, desaturate
approximately 0.8 and darken in the material; preserve local roughness variation
instead of making every stone mirror-smooth. Suggested values are in the
surface manifest. Fabric UV scale can follow the character mesh convention:
at one UV unit per metre, multiply UV by about 3.94 for its real weave scale.

## Verification

Downloaded texture bytes and MD5 match the official API; image signatures and
2048 × 2048 decoding passed. `verification.json` records a fresh Blender FBX
roundtrip with matched triangles, bounds, slots, UVs and vertex colors.

`preview_surface_v2.png` is a **Blender inspection render**, not an Unreal
result or a claim about in-game performance. `AshWell_SurfaceV2_Source.blend`
and the reproducible build/verification scripts are retained here.
