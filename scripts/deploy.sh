#!/bin/bash

# Shopnoltd K8s Platform - Complete Deployment Script
# This script deploys the full platform with all core services

set -e

echo "========================================="
echo "Shopnoltd K8s Platform - Deployment"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl not found${NC}"
    exit 1
fi

KUBE_CONTEXT=$(kubectl config current-context)
echo -e "${GREEN}Using Kubernetes context: $KUBE_CONTEXT${NC}"

# Step 1: Create namespaces
echo -e "\n${YELLOW}[1/6] Creating namespaces...${NC}"
kubectl apply -f config/namespaces.yaml
echo -e "${GREEN}✓ Namespaces created${NC}"

# Step 2: Install cert-manager
echo -e "\n${YELLOW}[2/6] Installing cert-manager...${NC}"
kubectl apply -f cluster/addons/cert-manager.yaml
echo -e "${GREEN}✓ Cert-manager installed${NC}"
sleep 5

# Step 3: Install ingress-nginx
echo -e "\n${YELLOW}[3/6] Installing NGINX Ingress Controller...${NC}"
kubectl apply -f cluster/ingress/nginx.yaml
sleep 10
echo -e "${GREEN}✓ NGINX Ingress installed${NC}"

# Step 4: Setup Cloudflare Tunnel
echo -e "\n${YELLOW}[4/6] Setting up Cloudflare Tunnel...${NC}"
echo -e "${YELLOW}Enter your Cloudflare Tunnel Token (from tunnel.cloudflare.com):${NC}"
read -s TUNNEL_TOKEN

kubectl create secret generic cloudflared-global-secret \
  -n kube-system \
  --from-literal=TUNNEL_TOKEN="$TUNNEL_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f cluster/addons/cloudflared-global-deployment.yaml
kubectl apply -f cluster/addons/cloudflared-global/configmap.yaml
echo -e "${GREEN}✓ Cloudflare Tunnel configured${NC}"
sleep 5

# Step 5: Install ArgoCD
echo -e "\n${YELLOW}[5/6] Installing ArgoCD...${NC}"
kubectl apply -f gitops/argocd/install.yaml
sleep 10
echo -e "${GREEN}✓ ArgoCD installed${NC}"

# Step 6: Deploy Ingress Routes
echo -e "\n${YELLOW}[6/6] Deploying ingress routes...${NC}"
kubectl apply -k gitops/ingress/
echo -e "${GREEN}✓ Ingress routes configured${NC}"

# Verification
echo -e "\n${YELLOW}Verifying deployment...${NC}"
sleep 5

echo -e "\n${GREEN}========== DEPLOYMENT STATUS ==========${NC}"

echo -e "\n${YELLOW}Namespaces:${NC}"
kubectl get ns | grep -E "kube-system|ingress-nginx|argocd|kobo|erp|mail|storage|monitoring|portainer|realtime" || echo "Not all namespaces ready"

echo -e "\n${YELLOW}Ingress Controllers:${NC}"
kubectl get pods -n ingress-nginx | grep ingress-nginx-controller || echo "NGINX controller not ready"

echo -e "\n${YELLOW}Cloudflare Tunnel:${NC}"
kubectl get pods -n kube-system | grep cloudflared-global || echo "Cloudflared not running"

echo -e "\n${YELLOW}ArgoCD:${NC}"
kubectl get pods -n argocd | grep argocd-server || echo "ArgoCD not ready"

echo -e "\n${YELLOW}Ingress Routes:${NC}"
kubectl get ingress -A | tail -10 || echo "No ingresses found"

echo -e "\n${GREEN}========== NEXT STEPS ==========${NC}"
echo -e "1. Verify all pods are running:"
echo -e "   ${YELLOW}kubectl get pods -A${NC}"
echo -e "\n2. ArgoCD Access:"
echo -e "   ${YELLOW}kubectl port-forward -n argocd svc/argocd-server 8080:80${NC}"
echo -e "   Visit: https://localhost:8080 (skip cert warning)"
echo -e "\n3. Get ArgoCD admin password:"
echo -e "   ${YELLOW}kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d${NC}"
echo -e "\n4. Deploy applications via:"
echo -e "   ${YELLOW}kubectl apply -f gitops/root/root-app.yaml${NC}"
echo -e "   or access ArgoCD UI and sync applications"
echo -e "\n5. Test access:"
echo -e "   ${YELLOW}curl https://argocd.shopnoltd.dpdns.org${NC}"
echo -e "   ${YELLOW}curl https://kf.shopnoltd.dpdns.org${NC}"

echo -e "\n${GREEN}✓ Core platform deployed successfully!${NC}"
