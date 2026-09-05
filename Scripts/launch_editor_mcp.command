#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
exec "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PROJECT_DIR/AshWell.uproject" /Game/AshWell/Maps/FirstDescentIntro -ModelContextProtocolStartServer -ModelContextProtocolPort=8001 -NoSplash
