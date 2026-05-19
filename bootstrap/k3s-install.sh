#!/bin/bash
set -e

echo "[1/3] Installing K3s HA-ready base node..."

curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server \
  --write-kubeconfig-mode 644 \
  --disable traefik \
  --disable servicelb" sh -

echo "[2/3] Waiting for cluster..."
sleep 5

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

kubectl get nodes

echo "[3/3] K3s installation complete"
