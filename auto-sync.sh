#!/bin/bash
set -euo pipefail

LOCK="/tmp/k8s-platform-sync.lock"

# prevent parallel runs
if [ -f "$LOCK" ]; then
  echo "Sync already running"
  exit 0
fi

touch "$LOCK"

trap "rm -f $LOCK" EXIT

cd ~/k8s-platform

echo "🔄 GitHub → GitLab sync started: $(date)"

# get latest from GitHub
git fetch origin

# ensure we are clean
git checkout main
git reset --hard origin/main

# push to GitLab mirror
git push gitlab main --force-with-lease

echo "✅ Sync completed: $(date)"
