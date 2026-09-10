# Warden HQ playable asset preparation

Approved appearance comes from `/Users/rare/dev/ash-well-local3d/results/warden-hq-v01/warden_pbr.glb`. The source GLB and both texture atlases are copied byte-for-byte here. The generation experiment's Blender inspection lights and camera were not imported. This preparation does not redesign the character.

## Contents

- `warden_pbr.glb`: immutable copy of the accepted source; its SHA-256 is recorded in `warden_manifest.json`.
- `SM_WardenHQ_*.fbx`: twelve mesh-only files: body/head/shoulders/skirt, both upper arms, both forearms with hands, both thighs, both shins, both feet, and the independent hammer.
- `pbr_albedo_texture.png`: original 4096×4096 sRGB base color.
- `pbr_mr_texture.png`: original 4096×4096 linear packed texture; **G = roughness, B = metallic**.
- `WardenHQ_Prepared.blend`: assembled rest pose with packed textures and local inspection camera/lights. These inspection objects are not present in FBX exports.
- `warden_manifest.json`: exact coordinates, part bounds, counts, texture channels and source provenance.
- `rest_front.png`, `rest_threequarter.png`, `pose_windup_walk.png`: real Blender renders used to inspect preservation and rigid articulation.

## Mesh processing

The 249,998-triangle source was simplified to **162,498 exterior triangles**, retaining the existing UV atlas. Coincident geometric vertices were welded before simplification while preserving per-corner UVs; this avoids independently simplified UV-seam edges producing cracks.

Every simplified exterior face is assigned to exactly one segment. Dark inner caps cover newly exposed cut surfaces. Small isolated cuffs and knee fragments are assigned to their touching part rather than removed. Final segmented count, including caps: **164,389 triangles**. The overall silhouette, asymmetric shoulders, visor, coat and hammer shape are retained. No new detail is claimed.

## Exact Unreal coordinate contract

These files deliberately bypass automatic axis guessing:

- Blender inspection and FBX vertices use **right-handed centimeter coordinates**. The mesh is exported unchanged. Unreal's FBX importer performs its native right-handed to left-handed Y reflection even when `convert_scene=False`; this is required to preserve the approved visible handedness. An additional reflection at export would mirror the shoulder and weapon to the wrong side.
- **In UE: +X is forward; character right is +Y; +Z is up.** In the RH Blender inspection coordinates, character right is -Y. These distinct coordinate systems represent the same appearance.
- Character foot baseline is Z = 0 and body/head top is approximately Z = 270.
- All segment object origins, translations and rotations are zero; scales are one. Mesh vertices retain a common rest origin.
- Import using `convert_scene=False`, `convert_scene_unit=False`, `transform_vertex_to_absolute=True`, `import_uniform_scale=1`. Do not recenter meshes and do not generate per-segment collision. Gameplay keeps the existing Warden capsule.
- Export settings: Blender scene unit scale `.01`; `use_space_transform=False`, `axis_forward='X'`, `axis_up='Z'`, `apply_unit_scale=True`, `global_scale=1`; selected mesh only; no animation, skeleton, camera, light or inspection ground.
- Source-to-Blender/FBX RH mapping: `(-source.y, source.x - .105, source.z + .8940808176994324) * 143.30669732583596`.
- Source-to-UE LH mapping: `(-source.y, .105 - source.x, source.z + .8940808176994324) * 143.30669732583596`.
- Manifest `joints_cm` and each part's `bounds_cm` are final **UE LH** coordinates; `blender_rh_joints_cm` and `blender_rh_bounds_cm` retain the inspection equivalents. Do not reflect UE landmarks again at runtime. Imported mesh bounds must match `bounds_cm`.

`joints_cm` in the manifest contains shoulders, elbows, grips, hips, knees, ankles, hammer head and tip. Apply a rigid transform `T(animated_pivot) * R(rest_axis → animated_axis) * T(-rest_pivot)` to each common-origin mesh. Do not use the old primitive cylinder scaling on the imported armor. The raw rest hammer tip is 15 cm below the boot plane in the supplied pose; the playable carried pose needs sufficient elevation to clear the deck.

Material slot 0 is `M_WardenHQ_Surface`; slot 1, where present, is `M_WardenHQ_Inner`, a near-black rough cap surface. Unreal should explicitly build the PBR material from the copied textures rather than relying on FBX material translation.

## Visual review and limits

The assembled render preserves the accepted model and textures. The raised-hammer preview confirms independent hammer motion and no remaining floating inner cuff. This is **rigid procedural articulation**, not a finished skeletal rig or production retopology. Fingers remain part of the forearm. Large knee, ankle and shoulder bends can reveal dark joins; keep walking moderate and let feet follow the shin rotation to minimize ankle separation. The coat stays with the body and can intersect legs in exaggerated poses.

Reproduce with:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python /Users/rare/dev/ash-well-ue/Scripts/prepare_warden_hq.py
```

The script runs in a separate Blender process and never changes the interactive Blender session or the original generation directory.
