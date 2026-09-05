#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
ENGINE="/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
if [[ -d /Applications/Xcode-beta.app/Contents/Developer ]]; then
  export DEVELOPER_DIR=/Applications/Xcode-beta.app/Contents/Developer
fi
exec "$ENGINE" "$PROJECT_DIR/AshWell.uproject" -NoSplash
