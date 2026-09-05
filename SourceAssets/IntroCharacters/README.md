# Intro workers

Original detailed CharactersV2 workers, rebuilt at a foot-centred origin and skinned to a small shared-layout skeleton. This directory is independent of the approved static V2 figures.

- `SK_Intro_Protagonist.fbx`: 178 cm worker with right-hand lantern.
- `SK_Intro_Companion.fbx`: matching worker with left-hand lantern and an open right glove.
- `A_Intro_<Role>_Walk.fbx`: in-place 1.4-second cautious walk, 30 fps. Nominal travel is 51.4 cm/s.
- `A_Intro_<Role>_Idle.fbx`: 2.8-second small breathing loop.
- `A_Intro_Companion_StopSignal.fbx`: 3-second transition to raised right palm and a slight head turn; holds the completed gesture at the end.
- `A_Intro_Companion_SignalHold.fbx`: 2.8-second raised-hand breathing loop.

FBX source metres, +X forward, +Y right, +Z up; export -Y forward and Z up. The root is stationary at the feet. Six slots remain Cloth, DarkSteel, Rust, Amber, Leather, Canvas, with the original surface-density UV0.

Import skeletal meshes with scene/unit conversion enabled, no automatic skeleton detection override, no static mesh combine, no generated materials. Import animation-only FBX files against that character's imported skeleton. All export names and timing are in `manifest.json`.

Attach the movable point light to `lamp_light_R` on protagonist or `lamp_light_L` on companion at zero local offset. Those dedicated bones are at the centre of the lantern glass and follow its independent gentle swing. `lantern_R/L` are the suspension bones, not the glass centres.

The armature has 24 bones. Original modelling parts receive semantic weights before joining; sleeves blend across the elbows, trousers across the knees, and the long coat has two secondary bones. Feet alternate planted and lifted phases. The root never supplies actor movement. Blend from walking into the stop animation for roughly 0.2 seconds where the runtime supports it.

This is prototype procedural animation, not a final character rig or motion-capture performance. It has no cloth simulation or finger animation and is designed for restrained walking and this specific signal gesture. Do not use it for running, jumping, or extreme poses.

`build_intro_characters.py` reproduces the source blend, meshes, animation clips and manifest. `verify_intro.py` checks FBX roundtrip dimensions, complete normalized skin weights, bones, UVs, six slots, clip timing, and zero root drift. `render_qa.py` renders labelled Blender action inspection frames; files containing `NOT_UE` are geometry/animation QA only, not Unreal output.
