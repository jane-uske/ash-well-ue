# Community animation trial

Source: Quaternius, Universal Animation Library Standard (45-animation free edition).
Author's release: https://opengameart.org/content/universal-animation-library
Pack page: https://quaternius.com/packs/universalanimationlibrary.html
License: CC0 1.0, verbatim License.txt retained.
Downloaded 2026-09-06; ZIP SHA-256: 18ff1a7215f4852b320203e8aaf02a1578b5c8eef9027fbaedfcedc7b85a3ac2.

AnimationLibrary_Standard.glb is the unchanged Godot-format GLB from that release. The author also supplies an Unreal FBX; that unused alternative is retained only in the local Saved/AnimationTrial download cache to avoid duplicating the full library in source control.

The trial uses **Sword_Attack**, not an authored hammer animation. A simple local test hammer is rigidly skinned to DEF-hand.R. This is a controlled experiment with a community clip at 1.00x and 0.62x, not the approved Warden model, a finished retarget, or a claim that slowing a sword slash makes a heavy hammer attack.

Files:
- CommunityAnimationTrial.blend: mannequin, source animation library and test prop.
- SK_TrialMannequin.fbx: selected mannequin/rig/prop only, no inspection objects.
- A_Trial_SourceSlash.fbx: one exported clip, sampled at 24 fps (37 frames / 1.541667 seconds; original GLB clip ends at 36.8 frames).
- preparation.json: export metadata.

Preparation used Blender MCP to import the GLB, inspect the bones/actions, attach the prop and run Scripts/prepare_animation_trial.py. To reproduce from a fresh Blender file: import AnimationLibrary_Standard.glb, move its objects into a collection named AW_CommunityAnimation_Trial, then run that script. It expects the imported Rig and Mannequin names and refuses to duplicate an existing trial prop.

UE import/map assembly uses Scripts/build_animation_trial.py via a one-session editor Python helper. UE MCP controls Sequencer playback and captures the viewport. Scripts/launch_animation_trial.command opens the isolated looping comparison scene. Normal combat assets and gameplay are not replaced.

Assessment: useful to validate community animation import and whole-body motion. The original one-handed slash is comparatively light; reducing playback speed also slows the impact, so a purpose-authored hammer clip or separately adjusted anticipation/strike/recovery is still needed for the Warden.
