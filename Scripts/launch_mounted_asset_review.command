#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
exec "$PROJECT_DIR/Scripts/launch_mounted_boss.command" -MountedAssetReview -MountedReviewOrbit "$@"
