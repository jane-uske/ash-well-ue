# Ash Well — Unreal

UE 5.8.2 playable development baseline.

## Run

- `Scripts/launch_combat.command`: combat prototype. E powers the station, Tab locks on, left mouse attacks, Space dodges, R retries.
- `Scripts/launch_intro.command`: introduction.
- `Scripts/launch_editor_mcp.command`: editor and official MCP on localhost:8001. Close the old AshWell MCP editor first to free this port.

Build before first launch:

```sh
DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer '/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' AshWellEditor Mac Development "$PWD/AshWell.uproject" -WaitMutex -NoHotReloadFromIDE -architecture=arm64
```

## Contents

`Source` gameplay; `Content` Unreal assets; `SourceAssets` editable model/audio sources; `Scripts` build/import helpers; `Docs` design and verification history. Historical documents may mention previous paths or engine versions.

Git LFS manages binary assets. Install Git LFS and run `git lfs pull` after cloning. Binaries, caches and runtime output are excluded. No remote is configured yet. A local commit is not an off-device backup.

The browser prototype and UE 5.7 project remain in ../ash-well. This repository combines the tested 5.8 code/assets with the original editable sources and scripts.

Migration check: native arm64 Development editor build succeeded from this repository path. Runtime and MCP evidence in Docs/Verification were recorded on the equivalent pre-migration 5.8 project.
