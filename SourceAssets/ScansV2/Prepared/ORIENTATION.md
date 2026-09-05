# Prepared scan orientation

`rock_face_01` presents its intended rock face toward **source -Y**, with width
along X and height along Z. The photographed ledge/slope recedes and rises into
**+Y**. This is supported by both included Blender inspection renders and the
mesh normals: 13.724 m² has a predominantly -Y normal versus 0.181 m² toward
+Y. The substantial upward-facing area (37.259 m²) means this is an inclined
rock face/ledge scan, not a flat upright wall or a uniformly thick sealed block.

Use the -Y side as the visible facade. Hide or overlap scan boundaries and the
unphotographed back in surrounding rock. The inferred '+Y back-depth' is valid
as a placement direction, but should not be interpreted as a solid back wall.
Do not rotate the texture independently to compensate for object placement.

`rock_face_01_from_minus_y.png` and `rock_face_01_from_plus_y.png` were rendered
in Blender from corresponding sides and visually inspected. They are orientation
checks, not game-render screenshots.

Normalized exports preserve the original world-space geometry, UV coordinates,
material slots and custom normals. Only object transforms were baked; no
recentering, scaling, Y mirroring, geometry decimation, UV rotation or map editing
was applied. Source DirectX normal maps remain untouched; Unreal should use
`FlipGreenChannel = false`. FBX tangent export is enabled.

| Prepared file | Selected source object | Triangles | Material slot |
| --- | --- | --- | --- |
| `SM_Scan_RockFace01.fbx` | `rock_face_01` | 20,174 | `rock_face_01` |
| `SM_Scan_Boulder01_LOD0.fbx` | `boulder_01_LOD0` only | 66,122 | `boulder_01` |

Both objects have identity transforms and origin `(0,0,0)`. FBX metre scene
units use `axis_forward=-Y`, `axis_up=Z`. Independent fresh FBX re-imports passed
one-mesh selection, triangle count, UV coordinate multiset and world-bound
checks. Source files were read only. See `manifest.json` for file hashes and
exact bounds.
