# Mounted Boss asset experiment

No paid generation, API credentials, or changes to original Warden/Hero assets.

- Horse candidate: Quaternius Ultimate Animated Animal Pack, CC0, source https://quaternius.com/packs/ultimateanimatedanimals.html . Low polygon verification asset, not final realistic art.
- Realistic alternative inspected: https://blendswap.com/blend/28627 (fdoss001); download requires login. Original model identified by page comments as Tarnyloo https://blendswap.com/blend/17172 (CC-BY), so the derivative page CC0 badge alone is insufficient for no-attribution reuse. Not downloaded or used.
- Rider reuses existing WardenRig and WardenHQ materials with new runtime seated pose.
- Polearm and saddle are independent local geometry made for this experiment.

Coordinate contract: centimetres, horse feet z=0, forward +X, saddle seat z=175 cm. Polearm origin is grip, axis +X, tip x=195 cm and butt x=-85 cm.

## Prepared and checked

- Original horse downloaded from the public Drive folder linked by Quaternius's official pack page. Original file, CC0 license text and SHA-256 provenance are retained under this directory.
- `SK_Horse.fbx`: 1,093 vertices, 51 bones including a single added root; inherited IK/control constraints are evaluated then baked into ordinary transform channels. World bounds are 266.78 × 66.13 × 226.73 cm including the head and tail. The saddle sits above the approximately 165 cm high back.
- Ten separate 60 fps clips: Idle, Walk, Gallop, Death, Kick, Headbutt, Jump, GallopJump, HitLeft and HitRight. They preserve the source performances. There is no dedicated rear, stomp, stop or turning clip.
- All four baked foot positions were compared against evaluated original animations on every exported frame; worst discrepancy after correction is 0.000081 cm. This checks the conversion, not in-game foot sliding, body collision, or runtime synchronization.
- FBX mesh and Walk clip were reimported into a separate background Blender process: correct 2.6678 m overall length, 51 bones, 71 frames at 60 fps, animated foot positions. UE import still requires independent runtime verification.
- `horse-neutral-diagnostic.png` was rendered and visually inspected. Silhouette and pose are intact; the low polygon silhouette and simplified coat remain conspicuous. This is not a realistic final Boss mount.

## Movement calibration

The clips are in-place. Median backward support-foot speed, measured within 5 cm of each foot's lowest sampled height, gives Walk 114.13 cm/s and Gallop 477.34 cm/s. Nominal cycles are 1.1667 s / 133.15 cm and 0.6000 s / 286.40 cm respectively. Advance animation time from measured ground travel divided by that reference speed. These are starting measurements; acceleration, turning, slope contact and cadence transitions need actual UE inspection.

## Reproduction

Run `Scripts/build_mounted_asset_props.py`, `Scripts/prepare_mounted_asset_horse.py` and `Scripts/verify_mounted_asset_horse.py` in disposable background Blender sessions. Then run `Scripts/import_mounted_assets.py` through the single shared UE editor owner. The importer only writes `/Game/AshWell/Combat/MountedBoss` and updates that new skeleton reference pose. It never edits Warden, Hero, or their original animations.

## Seated rider correction

The initial actual UE screenshot showed nearly straight hanging legs. Numeric inspection confirmed each requested ankle was about 135 cm from its hip while the original two-segment leg only reaches about 91 cm. The runtime targets now use `(20, ±63, 38)` in the original rider frame, giving approximately 119° / 111° inner knee angles. The saddle component Z scale of 0.925 raises the stirrup bars to the solved boot soles without moving the seat origin.

`Scripts/verify_mounted_asset_seat.py` reproduces the same leg solve with the source parts in background Blender. `seated-legs-diagnostic.png` was visually inspected: bent knees and boot/stirrup proximity are established in this static assembly. This does not verify the runtime gait or upper-body attack pose. The reused Warden skirt still clips below the saddle, and the rider's detailed armour contrasts with the simplified horse.

## Reversible rider skirt derivative

`SK_MountedRider.fbx` / `MountedRiderPrepared.blend` derive from the original WardenRig. Only faces whose vertices are fully weighted to `Body` are clipped below original z=100 cm, just below the 102.3 cm pelvis. Five cut loops receive the existing dark inner material. All 29,669 non-Body vertices preserve their exact coordinates and weights; all original bone names and rest matrices are unchanged, and the original Warden source hash is unchanged. Evidence is `mounted-rider-preservation.json`.

`mounted-rider-trim-diagnostic.png` was visually inspected against the previous side view: the long strips entering the horse below the saddle are removed, with no new visible hole at the seat. This static background assembly does not establish runtime synchronization. Prepare with `Scripts/prepare_mounted_rider.py`; inspect with `Scripts/verify_mounted_rider.py` and `Scripts/verify_mounted_rider_preservation.py`; the shared UE owner imports with `Scripts/import_mounted_rider.py`. New runtime path is `/Game/AshWell/Combat/MountedBoss/SK_MountedRider`, with the same 11 driven part names and original material interfaces. The old Warden remains the fallback.
