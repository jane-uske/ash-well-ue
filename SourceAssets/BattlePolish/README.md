# BattlePolish authoring assets

The approved existing protagonist and Warden appearances are retained. No generated carrier mesh is imported into the game.

- `A_Battle_*.fbx`: four phase-remapped, in-place animations for `SK_Intro_Protagonist_Skeleton`.
- `BattlePlayerAnimations.blend`: compact source scene with the four actions.
- `BattlePolishGeometry.blend`, `SM_Battle*.fbx`: original lightweight vault and impact ring.
- `AW_Battle_*.wav`: original deterministic synthesis from `Scripts/build_battle_audio.py`, no outside samples. Parameters and levels in `audio-manifest.json`.
- `animation-manifest.json`: source presets, durations and target skeleton.

Meshy source tasks and downloads: `../../meshy_output/20260909_battle_motion_v01/`. The motion carrier is from Quaternius Universal Animation Library Standard, CC0; the original license is retained in `../AnimationTrial/`. Meshy animation output remains subject to the user's Meshy account terms. Existing Suno music remains under its separately recorded source terms; this work does not change that license.

Rebuild: `Scripts/retarget_battle_motion.py` and `Scripts/build_battle_polish_geometry.py` in Blender; `Scripts/chapter01_battleassets.py` via UE native MCP `run_stage("battleassets")`. FBX armature object root must be exactly `SK_Intro_Protagonist_Rig`, including when Blender has multiple scenes loaded. Asset imports never include scene cameras/lights.
