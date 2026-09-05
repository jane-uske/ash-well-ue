# Combat animation prototype

Original procedural animation for the existing `SK_Intro_Protagonist` worker. The
24-bone hierarchy and bind pose are unchanged. No Epic/game animation was copied.
The left hand swings a runtime-attached industrial hammer; the right hand retains
the lantern. These are prototype poses, with no motion capture or cloth solver.

| Clip suffix | Duration | Intended use |
| --- | ---: | --- |
| `Attack` | 0.833333 s | 0–0.30 anticipation; 0.30–0.45 hit window; 0.45–0.833 recovery |
| `Dodge` | 0.583333 s | Compact low dodge; supply capsule displacement and invulnerability in runtime |
| `Hit` | 0.45 s | Short backward recoil, returns to neutral |
| `Death` | 1.30 s | Backward fall; hold the final frame |
| `CombatWalk` | 0.60 s | Loop for 240 cm/s, two 72 cm steps per cycle |

Full names are `A_Combat_Protagonist_<suffix>`. All clips are in place, with an
identity root, sampled at 60 fps. The attack/dodge/recoil return to their initial
body pose. Small lantern settling is deliberately independent of the body.

Source coordinates are metres, +X forward, +Y right, +Z up. FBX export uses -Y
forward, Z up, metre scene units and the existing skeleton's Y primary bone axis.
Keep the current UE mesh transform used by the intro character. The weapon attaches
to `hand_L`; bone-local +Y points toward the fingers. The point light attaches at
zero offset to `lamp_light_R`, at the centre of the lantern glass.

Run `build_combat_animations.py` with Blender to reproduce the files. Run
`verify_combat_animations.py` for FBX round-trip duration, hierarchy, finite-pose,
stationary-root and loop checks, then keyframe renders. `verification.json` and
`pose-review.json` report those checks. Images named `NOT_UE` are Blender source
pose checks and do not demonstrate UE runtime import or rendering.

The original `.blend` preview's player armature modifier had been applied during
its second-character build. This package restores the modifier using the existing
vertex weights in its own `CombatAnimations.blend` only. The original Intro source,
mesh FBX and skeleton are unchanged.

UE import: run `Scripts/import_combat_animations.py` in the editor. It uses the
existing `/Game/AshWell/Intro/Characters/SK_Intro_Protagonist_Skeleton`, imports only
animations into `/Game/AshWell/Combat/Characters`, uses a 60 Hz custom sample rate,
disables root motion, and asserts each duration. It writes the separate runtime
asset report to `Saved/Automation/combat-animations-report.json`.
