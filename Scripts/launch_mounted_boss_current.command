#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
# Current mounted encounter: natural AI, full health, ordinary player controls.
# No single-action review or deterministic QA flags are enabled here.
exec "$PROJECT_DIR/Scripts/launch_mounted_charge_sample.command" "$@"
