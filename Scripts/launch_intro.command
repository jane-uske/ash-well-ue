#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
ENGINE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
exec "$ENGINE" "$PROJECT_DIR/AshWell.uproject" /Game/AshWell/Maps/FirstDescentIntro -game -windowed -ResX=1600 -ResY=900 -NoSplash
