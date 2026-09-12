#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
exec "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PROJECT_DIR/AshWell.uproject" /Game/AshWell/MountedBoss/L_MountedCourtyard -game -windowed "-ResX=${ASHWELL_RES_X:-1600}" "-ResY=${ASHWELL_RES_Y:-900}" -NoSplash -CombatPrototype -MountedExperiment -MountedDebug -DisablePlugins=AllToolsets,ModelContextProtocol "$@"
