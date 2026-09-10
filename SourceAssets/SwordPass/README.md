# SwordPass source assets

Approved appearance: `../../Docs/ArtDirection/Characters/hero-turnaround-v01.png`.
The uncloaked T-pose image is an intermediate only. Source Meshy outputs and task IDs are listed in `../../Docs/Implementation/sword-traveller-v01.md`.

## Provenance

- Base body and skin weights: Meshy image-to-3D and auto-rig from the original reference (30 + 5 credits). Body 31,198 triangles; independent cloak approximately 1,664 triangles. 2048 px base, metallic/roughness and normal textures.
- Idle/walk/run/sprint/guard/combat walk: existing Quaternius Standard CC0 library; license preserved at `../AnimationTrial/License.txt`. Upper-body slash/heavy targets and long sword are local authored work.
- Cloak/collar and sword/scabbard: original Blender geometry. No scene cameras/lights are exported as game assets.
- The supplied Meshy walk/run GLBs are retained in meshy_output but not the active locomotion clips.

## Rebuild order

1. Blender: load existing protagonist rig, CC0 AnimationLibrary_Standard.glb; `build_sword_motion.py` retargets sampled transforms to the existing skeleton. `build_traveller_sword.py` exports separate weapon meshes.
2. Load the original Meshy GLB as `Mesh_0` and auto-rig as `TravellerSourceRig` + child `char1`. `prepare_traveller.py` transfers joints/weights onto a copy of `SK_Intro_Protagonist_Rig`, adds separate skinned cloak, exports FBX and TravellerPrepared.blend. Scripts expect the named input objects; inspect before running in a different Blender session.
3. UE native MCP `ChapterOneTools.run_stage("swordassets")` calls chapter01_swordassets.py and import_traveller.py. Legacy FBX import is explicitly selected for deterministic units/reimports. Import report and root-scale assertions are in Saved/SwordPass.

## Integration constraints

- Existing FBX hierarchy root must be named SK_Intro_Protagonist_Rig. The animation root uses scale 100. Imported raw mesh bounds do not cover the deformed 180 cm body; explicit measured bounds extensions prevent frustum culling during sprint. This is compatibility with the existing project, not a recommended new skeleton convention.
- Player component mirrors Y; weapon uses hand_L. Sword import long axis is UE +X, blade 14..101 cm. Grip offsets use socket rotation without inheriting its 100x scale.
- Reimported render sections can use material index 1. Preserve/assign both material slots, rather than shrinking to slot 0 only.
- The inherited skin's tangent lighting produced severe black/bright facets on Mac UE. Verified unlit/base-color and geometric-normal comparisons isolated lighting from the texture. Current lit body/cape materials derive geometric normals from world-position derivatives. Source normal texture is retained but not the active surface normal. This is a v01 compatibility solution; normalize/rebuild the skeleton and tangent data before close-up character art acceptance.
- Cloth is skinned, not simulated. Fingers have no articulated rig; grip is a static glove deformation. Face likeness, folded hood/cape shape, all-direction foot planting and extreme-pose intersections are unfinished.

## Verification

Scripts/test_battle_runtime.py launches actual UE windows. Scripts/test_sword_pass.py checks zero-stamina rules, six locomotion selections, body scale and blade attachment in five poses. See Docs/Verification/SwordPass. Passing telemetry does not certify visual quality or human difficulty.

Rollback: local Saved/SwordPass/before-sword-pass.zip preserves pre-turn source/config/scripts. -SwordBaseline selects previous assets and timing for comparison; no packaging/commit was performed.
