#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
exec "$PROJECT_DIR/Scripts/launch_station_gate.command" -BattleBaseline "$@"
