# Expedition figures V2

These original static character meshes revise the silhouettes against the concept image and the actual first UE frame. Geometry now uses a soft storm collar and collapsed half hood, restrained shoulder plates, irregular clothing folds, a canvas field pack with wide webbing and buckles, one small oxygen bottle, a ground-sheet roll, repair cord and tool. Gloved fingers curl around the lantern bail. A slight hip lean is baked into the stance.

The two FBX files retain the V1 names. Each has one combined mesh at origin zero, with the world placement baked into its vertices. Put both UE actors at world origin when using these baked positions. Source axes are +X forward, +Y right and +Z up, in metres. FBX export uses `-Y` forward, `Z` up, with metre scene units; verify source-to-UE axis conversion on import. Final height is approximately 1.78 m; soles are 1 mm above the nominal ground plane.

Material slots, in order: **Cloth, DarkSteel, Rust, Amber, Leather, Canvas**. The new Canvas slot covers the old field pack, webbing and woven reinforcement; the balaclava and cowl use Cloth. DarkSteel is intended as dark, worn and mostly rough metal, not chrome. Surface textures and tangent-space normals should be bound in UE.

UV0 is generated from the completed geometry with equalized island scale, then normalized to approximately **1 metre per UV unit**. UV coordinates intentionally tile beyond 0–1. A texture representing 0.254 m of real surface should use a TextureCoordinate multiplier near **3.937**. The mapping is a surface-material layer, not a packed lightmap; UE may generate a separate lightmap UV if needed. `manifest.json` records the precise surface and UV areas.

Lantern centres in source metres are recorded in the manifest. Multiply by 100 for UE centimetres when the import preserves the source axes. Do not apply character offsets again to those world positions.

`build_expedition_figures.py` recreates the FBX files and `.blend`. `verify_expedition_fbx.py` independently reimports the FBX and checks triangle counts, bounds, all six material slots, finite UVs, and UV area preservation; results are in `verification.json`.

`qa_geometry.py` and `qa_geometry_NOT_UE.png` are an internal neutral Workbench inspection of the actual mesh, used to correct the collar and fold distribution. **That image is not a UE render or a finished-game screenshot.** Final UE materials, lighting, scene placement and image acceptance remain to be verified in the engine. These characters are static set dressing, without a rig or animation.
