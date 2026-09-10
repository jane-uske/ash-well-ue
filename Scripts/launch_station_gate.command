#!/bin/zsh
set -e
SCRIPT_DIR="${0:A:h}"
exec "$SCRIPT_DIR/launch_chapter01.command" -ChapterGatePreview "$@"
