#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
exec python3 "$PROJECT_DIR/Scripts/run_mounted_human_test.py"
