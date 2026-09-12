#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export ASHWELL_RES_X=1920 ASHWELL_RES_Y=1080
exec "$PROJECT_DIR/Scripts/launch_mounted_boss.command" -MountedChargeSample -MountedFootPlacement "$@"
