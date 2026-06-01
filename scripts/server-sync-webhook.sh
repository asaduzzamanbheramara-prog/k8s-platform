#!/bin/bash
# server-sync-webhook.sh - Webhook handler for automatic server sync

set -euo pipefail

REPO_DIR="/home/shopno/k8s-platform"
LOG_FILE="/var/log/k8s-webhooks/server-sync.log"
LOCK_FILE="/tmp/k8s-sync-webhook.lock"

mkdir -p /var/log/k8s-webhooks 2>/dev/null || true

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$1] $2" >> "$LOG_FILE" 2>&1 || true
}

# Check lock
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c%Y "$LOCK_FILE" 2>/dev/null || echo 0)))
    if [ "$LOCK_AGE" -lt 1800 ]; then
        log "WARN" "Sync already running"
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi

touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log "INFO" "=== Webhook triggered, starting sync ==="

cd "$REPO_DIR"

# Fetch and reset
log "INFO" "Fetching from origin"
git fetch origin

# Determine branch - default to main
BRANCH="main"
if [ -f "/tmp/webhook-branch.txt" ]; then
    BRANCH=$(cat /tmp/webhook-branch.txt)
    rm /tmp/webhook-branch.txt
fi

log "INFO" "Syncing branch: $BRANCH"

git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null || true
git reset --hard "origin/$BRANCH"

log "INFO" "Deploying Kubernetes manifests"

# Apply manifests
for dir in k8s/{namespaces,rbac,configmaps,secrets,deployments,services,ingress,jobs}; do
    if [ -d "$dir" ]; then
        log "INFO" "Applying $dir"
        kubectl apply -f "$dir" -R --record 2>&1 || log "ERROR" "Failed to apply $dir"
    fi
done

# Verify
PENDING=$(kubectl get pods -A --field-selector=status.phase=Pending -o json 2>/dev/null | grep -c "name" || echo "0")
FAILED=$(kubectl get pods -A --field-selector=status.phase=Failed -o json 2>/dev/null | grep -c "name" || echo "0")

if [ "$FAILED" -gt 0 ]; then
    log "ERROR" "Found $FAILED failed pods"
else
    log "INFO" "Deployment verification passed"
fi

# Sync GitLab mirror
if git remote | grep -q gitlab; then
    git push gitlab "$BRANCH" --force-with-lease 2>/dev/null || log "WARN" "GitLab mirror push failed"
fi

log "INFO" "=== Sync completed successfully ==="
