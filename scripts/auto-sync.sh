#!/bin/bash
set -euo pipefail

LOCK="/tmp/k8s-platform-sync.lock"

if [ -f "$LOCK" ]; then
  echo "Sync already running"
  exit 0
fi

touch "$LOCK"
trap "rm -f $LOCK" EXIT

cd ~/k8s-platform

echo "🔄 GitHub → GitLab sync started: $(date)"

# -------------------------------
# 1. Sync latest code
# -------------------------------
git fetch origin
git checkout main
git reset --hard origin/main

# -------------------------------
# 2. SAFE VALIDATION (IMPORTANT)
# -------------------------------
echo "🔍 Validating GitOps structure..."

if [ ! -d "gitops/ingress" ]; then
  echo "❌ ERROR: gitops/ingress missing"
  echo "👉 Domain registry generator is broken or not committed"
  exit 1
fi

if [ ! -d "gitops/appsets" ]; then
  echo "❌ ERROR: gitops/appsets missing"
  exit 1
fi

if [ ! -f "gitops/appsets/platform-services.yaml" ]; then
  echo "❌ ERROR: platform-services.yaml missing"
  exit 1
fi

# -------------------------------
# 3. ENSURE ROOT EXISTS (NO COPY, NO RSYNC)
# -------------------------------
mkdir -p gitops/root

cat > gitops/root/kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../appsets/platform-services.yaml
  - ../ingress
