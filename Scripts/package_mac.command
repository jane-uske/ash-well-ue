#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
ENGINE_ROOT='/Users/Shared/Epic Games/UE_5.8'
"$ENGINE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
 -project="$PROJECT_DIR/AshWell.uproject" -noP4 -platform=Mac \
 -clientconfig=Development -ubtargs=-NoUBA -build -cook -stage -pak -iostore -archive \
 -archivedirectory="$PROJECT_DIR/Artifacts/InspectionStation" \
 -map=/Game/AshWell/Maps/FirstDescentIntro -utf8output -unattended "$@"
