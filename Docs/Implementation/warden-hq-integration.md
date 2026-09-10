# Approved Warden HQ — first playable integration

Uses the user-approved local asset from `ash-well-local3d/results/warden-hq-v01/warden_pbr.glb`. Original geometry and 4K color/MR textures are preserved in SourceAssets/WardenHQ; the supplied Blender inspection scene's cameras and lights are not imported.

## Asset adaptation

249,998 source triangles reduced to 162,498 exterior / 164,389 including seam caps. Twelve separately imported rigid parts: torso with head/shoulders/coat, two upper arms, two forearms with hands, two thighs, two shins, two feet, and hammer. UV seams are welded geometrically before decimation while retaining per-corner UVs. Original files are retained; preparation is reproducible with Scripts/prepare_warden_hq.py.

Material: color RGB is sRGB; packed roughness G and metallic B are linear. Cut interiors use a separate dark material. Meshes have no gameplay collision; the existing capsule remains authoritative.

## Animation adaptation

The generated meshes are driven separately from hidden prototype pose components. Two-bone IK keeps armour segments rigid and attached. A waist hinge supplies the forward reach the shorter generated arms require. The hammer retains its native length: its shaft direction is constrained to a reachable cone while its head follows the original attack trajectory. The old negative-Y “right arm” is reflected only for the generated visual to preserve the approved asset's anatomical handedness. Gameplay facing, movement and attack logic remain unchanged.

The new meshes are **not a fully skinned production character**. Shoulders/knees have visible rigid joins at extreme angles; the long coat has no cloth simulation; fingers remain part of the forearms. These are accepted first-playable limitations, not evidence of finished animation quality.

## Running and verification

Use Scripts/launch_combat.command. The existing E / Tab / left mouse / Space / R controls remain. `-WardenPrimitive` retains a comparison fallback. Default loads all12generated parts and PBR; any missing required part triggers a complete primitive fallback with a log warning.

`-CombatQA` runs the existing fight and records snapshots/screenshots. Add `-WardenDeathQA` to stand through damage, then call the same controller restart function bound to R and verify the fresh state. This is an automated function-path test, not a manual key-input test.

Source invariants: Scripts/verify_warden_gameplay.py compares 38 protected rules/functions to commit 65a681b. Asset importer checks all 12 bounds against the manifest. Runtime evidence and pose captures are collected under Saved/Automation and Saved/Screenshots/WardenHQ; checked final results are in [Docs/Verification/WardenHQ](../Verification/WardenHQ/README.md).

The standalone launcher excludes the editor-only AllToolsets / ModelContextProtocol plugins from the game process. Both remain enabled for the normal editor/MCP workflow. Additional launch arguments are forwarded, including the optional QA flags above.

UE 5.8's unattended FBX reimport can replace task options with settings stored on an existing mesh. The importer recreates only its own twelve generated assets and verifies every imported minimum/maximum bound within 0.02 cm. This avoids carrying stale axis settings into another generated pass.
