#!/usr/bin/env bash
set -euo pipefail

# Auto-start helper for WSL: Docker, cloudflared, k3s/kubelet and quick health checks
# Place this at /home/shopno/k8s-platform/bootstrap/auto_start_wsl.sh and make executable.

BASE_DIR="/home/shopno/k8s-platform"
CHECK_SCRIPT="$BASE_DIR/check-domains.sh"

echo "== Auto-start helper =="

if grep -q "\[boot\]" /etc/wsl.conf 2>/dev/null; then
  echo "systemd likely enabled in WSL (check /etc/wsl.conf)."
else
  echo "Note: systemd not detected in /etc/wsl.conf — services may not persist across WSL restarts."
  echo "To enable systemd, add these lines to /etc/wsl.conf and run 'wsl --shutdown' from Windows PowerShell:"
  echo
  echo "[boot]"
  echo "systemd=true"
  echo
fi

echo "Starting Docker if available..."
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl start docker || true
else
  # try to background dockerd
  if pgrep -x dockerd >/dev/null 2>&1; then
    echo "dockerd already running"
  else
    echo "Starting dockerd in background..."
    sudo nohup /usr/bin/dockerd >/tmp/dockerd.log 2>&1 &
  fi
fi

echo "Starting cloudflared service (if installed)..."
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl start cloudflared || echo "cloudflared systemd unit not found"
else
  echo "systemctl not available — ensure cloudflared is started by other means (k8s or manual)."
fi

echo "Starting k3s/kubelet if present..."
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl start k3s || sudo systemctl start kubelet || echo "k3s/kubelet unit not found"
fi

echo "Waiting for Kubernetes API (if kubeconfig is present)..."
WAIT=0
if kubectl version --client >/dev/null 2>&1; then
  until kubectl get nodes >/dev/null 2>&1 || [ $WAIT -ge 30 ]; do
    echo -n "."
    sleep 2
    WAIT=$((WAIT+1))
  done
  echo
  if [ $WAIT -ge 30 ]; then
    echo "Kubernetes API not ready after wait"
  else
    echo "Kubernetes API reachable"
    echo "Restarting key deployments (argocd, cloudflared, ingress) if present..."
    kubectl -n kube-system rollout status deploy --timeout=10s || true
  fi
else
  echo "kubectl not found or not configured — skipping k8s checks"
fi

echo "Running domain & service health check: $CHECK_SCRIPT"
if [ -x "$CHECK_SCRIPT" ]; then
  bash "$CHECK_SCRIPT"
else
  echo "Check script not executable or missing. Ensure $CHECK_SCRIPT exists and is executable."
fi

echo "== Auto-start complete =="
