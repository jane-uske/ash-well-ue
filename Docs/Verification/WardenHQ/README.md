# Warden HQ playable integration — verified 2026-09-06

Actual standalone Unreal Engine 5.8.2 build, macOS arm64, 1600 × 900. The checked images are engine screenshots from the final correctly oriented imported model, not Blender renders or concept art.

| Check | Result | Evidence |
| --- | --- | --- |
| Editor target build | Passed, Development arm64 | Build completed successfully before runtime passes |
| Asset import | 12 static parts, all bounds match manifest within 0.02 cm; 4K PBR material; no inspection lights/cameras | [import-result.json](import-result.json) |
| Gameplay preservation | All 38 source guards passed against baseline 65a681b | [source-regression.json](source-regression.json) |
| Fixed-length hammer adaptation | All three phases reachable, 10,001 samples per phase; theoretical maximum head residual 3.83e-14 cm | [retarget-audit.json](retarget-audit.json) |
| Actual fight | Victory; six hits; eight attacks; 19 dodges; 15 evaded strikes; player HP 65; Boss HP 0 | [win-result.json](win-result.json) |
| Player death | Three received strikes; HP 0; dead state; all 12 generated parts loaded | [death-result.json](death-result.json) |
| Restart | Existing controller restart function reloaded the map; player HP 100; Boss HP 240; power off; encounter inactive | [reset-result.json](reset-result.json) |

The final win and death/reset process logs each had zero `Error:` or fatal-error entries. Retained runtime hammer residuals are below 0.00001 cm. These individual runtime samples supplement the numerical trajectory audit; they are not a frame-by-frame performance benchmark.

## Visual checks

- [Raised.png](Raised.png): asymmetrical slab shoulder and hammer are on the approved side; PBR is visible under the station's actual lighting; raised attack remains readable.
- [Slam.png](Slam.png): the character leans into the ground strike and retains the independent hammer.
- [Defeated.png](Defeated.png): captured at the first defeated state; this image does not establish the completion of the subsequent fall animation.

Restart QA calls the same `IntroRestart()` function bound to R. It does not synthesize a physical R key press. The normal E / Tab / left mouse / Space / R input bindings were preserved by the source guard checks.

## Scope and remaining limitations

This is the requested first playable asset integration. The approved source was reduced from 249,998 triangles to 164,389 including cut caps, and split into twelve rigid parts. No visual redesign or production skeletal rig was introduced. Shoulder/knee joins can show under extreme bends; the coat remains rigid and can intersect the legs. Further animation refinement and performance profiling remain future work.
