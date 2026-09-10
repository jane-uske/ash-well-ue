#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
exec "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PROJECT_DIR/AshWell.uproject" /Game/AshWell/Chapter01/L_Chapter01_Descent -game -windowed -ResX=1600 -ResY=900 -NoSplash -CombatPrototype -DisablePlugins=AllToolsets,ModelContextProtocol "$@"
