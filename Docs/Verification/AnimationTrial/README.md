# Community animation trial — 2026-09-06

Blender 5.2 MCP: connected; inspected the source action list and 53 bones; exported mannequin and test prop with Sword_Attack.

UE 5.8.2: imported the skeletal mesh and 1.541667-second clip; constructed an isolated comparison map and autoplaying Level Sequence. Left is the source motion at 1.00x, right is the same motion at 0.62x. Both carry the same simple hammer to keep the comparison controlled.

UE MCP: successfully opened/controlled Sequencer, queried frame positions, captured the editor viewport and resumed loop playback. Captures may retain editor overlays and cached poses; they are not frame-accurate animation evidence. The MCP verification JSON confirms control responses, not skeletal retarget quality.

Normal game launch: Scripts/launch_animation_trial.command. This is an animation viewer, not a replacement for the playable Boss encounter. No combat timings, player controls or Warden mesh assets are changed in this trial.

Final standalone verification: launched in a fresh process after explicitly saving the generated Skeleton asset. The comparison map loaded successfully with zero `Error:` or fatal-error entries in Saved/AnimationTrial/standalone-final.log. Two live UI observations showed different raised/recovery poses. `runtime.png` is the actual 1600x900 standalone screenshot saved with F9, without editor overlays. The trial window was left running for the user.

The 38 existing combat source guards still pass. Four new Python scripts parse successfully and the standalone launcher passes zsh syntax validation. No C++ changes or new compilation were needed for this animation-only trial.

Source and license: see SourceAssets/AnimationTrial/README.md and License.txt. No paid animation pack was purchased or imported.
