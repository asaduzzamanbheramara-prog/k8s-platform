# 🚀 Shopnoltd K8s Platform - Complete Setup Guide

## 📋 Overview

This guide provides comprehensive step-by-step instructions for setting up the complete Shopnoltd Kubernetes platform with domain browsability, auto-sync webhooks, and full infrastructure deployment.

**Target Audience**: DevOps Engineers, Platform Administrators  
**Estimated Time**: 2-3 hours  
**Prerequisites Knowledge**: Kubernetes, Git, DNS, Docker

---

## ✅ Prerequisites Checklist

Before starting setup, ensure you have:

### System Requirements
- [ ] Linux/WSL2 environment with 4GB+ RAM
- [ ] kubectl CLI installed (v1.24+)
- [ ] git installed and configured
- [ ] docker or docker CLI
- [ ] curl and wget tools
- [ ] Domain: shopnoltd.dpdns.org (DNS configured at FreeDNS)
- [ ] Cloudflare Tunnel token (from https://dash.cloudflare.com/)

### Git Configuration
- [ ] GitHub account with SSH key configured
- [ ] GitLab account (optional, for mirror)
- [ ] Repository forked/cloned: asaduzzamanbheramara-prog/k8s-platform

### Credentials & Secrets
- [ ] Cloudflare Tunnel Token (saved in secure location)
- [ ] GitHub Personal Access Token (for webhooks)
- [ ] GitLab Personal Access Token (if using GitLab mirror)
- [ ] SSH keys for server authentication
- [ ] Database credentials (if needed)

### Access Requirements
- [ ] Cluster access (local or remote)
- [ ] Namespace creation permissions
- [ ] Ingress controller access
- [ ] Cert-manager permissions
- [ ] DNS management access

### Verification Script
``ash
# Run this to verify prerequisites
./scripts/verify-prerequisites.sh
``

---

## 📝 Step-by-Step Setup Instructions

### Phase 1: Git & Repository Setup

#### Step 1a: Fix Git Ownership ✅ COMPLETED
**Status**: Already Done  
**What was done**: Git repository ownership fixed  
**No action needed**

#### Step 1b: Configure GitHub Remote ✅ COMPLETED  
**Status**: Already Done  
**Repository**: asaduzzamanbheramara-prog/k8s-platform  
**Remote URL**: git@github.com:asaduzzamanbheramara-prog/k8s-platform.git  

**Verification**:
``ash
git remote -v
# Output should show origin pointing to GitHub
``

#### Step 1c: Configure GitLab Remote ⏳ BLOCKED
**Status**: Needs GitLab URL  
**Issue**: GitLab mirror URL not configured  
**Action Required**: Provide GitLab repository URL

**Setup Instructions**:
``ash
# Add GitLab remote (when URL available)
git remote add gitlab https://gitlab.com/shopnoltd/k8s-platform.git

# Or with SSH (if SSH keys configured)
git remote add gitlab git@gitlab.com:shopnoltd/k8s-platform.git

# Verify
git remote -v
``

---

### Phase 2: Kubernetes Cluster Setup

#### Step 2a: Start Kubernetes Cluster ⏳ BLOCKED
**Status**: Requires cluster  
**Prerequisites**: None met yet  
**Action Required**: Choose and provision cluster

#### Option 1: Local K3s (Development)
``ash
# Install K3s (single node)
curl -sfL https://get.k3s.io | sh -

# Verify installation
kubectl cluster-info
kubectl get nodes

# Default kubeconfig location: /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
``

#### Option 2: Kubernetes Desktop (Docker Desktop, Minikube)
``ash
# Docker Desktop
# Settings → Kubernetes → Enable Kubernetes ✓

# Or Minikube
minikube start --cpus=4 --memory=8192 --disk-size=50gb

# Verify
kubectl cluster-info
``

#### Option 3: Cloud Kubernetes (AWS EKS, GKE, AKS)
``ash
# AWS EKS Example
eksctl create cluster --name shopnoltd-k8s --region us-east-1 --nodes=3

# Configure kubectl
aws eks update-kubeconfig --name shopnoltd-k8s --region us-east-1
``

#### Step 2b: Deploy Kubernetes Ingress ✅ READY (Awaiting Cluster)
**Status**: Manifests prepared, ready to deploy  
**Components**:
- NGINX Ingress Controller
- Cert-Manager with Let's Encrypt
- Ingress resources (9 total)

**Deployment**:
``ash
# Deploy all infrastructure
cd /home/shopno/k8s-platform

# Run automated deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# When prompted:
# - Enter Cloudflare Tunnel Token: (paste your token)
# - Confirm deployments: yes

# Verify deployment
kubectl get pods -a
kubectl get ingress -a
kubectl get certificates -a
``

**What Gets Deployed**:
- Namespaces (10 total)
- NGINX Ingress Controller
- Cert-Manager
- Cloudflare Tunnel
- 9 Ingress resources
- ArgoCD (optional)

---

### Phase 3: DNS & Domain Configuration

#### Step 3a: Configure DNS Records ✅ READY
**Status**: Already configured at FreeDNS  
**Domain**: shopnoltd.dpdns.org  
**Total Records**: 25+ subdomains  

**DNS Records Configured**:
``
shopnoltd.dpdns.org            A → Cloudflare Tunnel IP
*.shopnoltd.dpdns.org          A → Cloudflare Tunnel IP

Specific subdomains:
toolbox.shopnoltd.dpdns.org    CNAME → shopnoltd.dpdns.org
erp.shopnoltd.dpdns.org        CNAME → shopnoltd.dpdns.org
mail.shopnoltd.dpdns.org       CNAME → shopnoltd.dpdns.org
... (22+ more)
``

**Verification**:
``ash
# Test DNS resolution
nslookup shopnoltd.dpdns.org
nslookup toolbox.shopnoltd.dpdns.org
nslookup grafana.shopnoltd.dpdns.org

# Expected: All resolve to same IP (Cloudflare Tunnel endpoint)
``

#### Step 3b: DNS Propagation Check
``ash
# Full propagation check
./scripts/check-domains.sh

# Expected output:
# ✓ shopnoltd.dpdns.org resolves
# ✓ toolbox.shopnoltd.dpdns.org resolves
# ✓ erp.shopnoltd.dpdns.org resolves
# ... (all 25+ domains)
``

---

### Phase 4: Webhook & Auto-Sync Setup

#### Step 4a: Setup Webhook Server ✅ READY (With Script)
**Status**: Automated setup available  
**Components**: Python webhook server, systemd service  

**Deployment**:
``ash
# Copy webhook server script
cp scripts/webhook-server.py /opt/webhook-server/webhook-server.py

# Copy systemd service
sudo cp scripts/k8s-webhook.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable k8s-webhook
sudo systemctl start k8s-webhook

# Verify running
sudo systemctl status k8s-webhook
curl http://localhost:5000/health
``

**Webhook Server Configuration**:
``yaml
Port: 5000
Health Endpoint: /health
GitHub Webhook: /webhook/github
GitLab Webhook: /webhook/gitlab
Sync Action: Triggers auto-sync to K8s
``

#### Step 4b: Configure GitHub Webhooks
**GitHub Setup**:
1. Go to: Settings → Webhooks → Add webhook
2. Configure:
   - Payload URL: https://your-server.com/webhook/github
   - Content Type: pplication/json
   - Events: Push events, Pull request events
   - Active: ✓ Checked
3. Add Secret: (use GitHub secret from config)

**Verification**:
``ash
# Check webhook logs
sudo journalctl -u k8s-webhook -f

# Expected on push:
# [INFO] Received GitHub webhook
# [INFO] Syncing repository
# [INFO] Deploying to K8s
``

#### Step 4c: Configure GitLab Webhooks (Optional)
**GitLab Setup**:
1. Go to: Settings → Webhooks → Add webhook
2. Configure:
   - URL: https://your-server.com/webhook/gitlab
   - Trigger: Push events
   - SSL verification: Enabled
3. Add Token: (use GitLab token from secrets)

---

### Phase 5: Secret Configuration

#### Step 5a: Configure GitHub Secrets
**Required Secrets**:
``yaml
GITHUB_TOKEN: Personal Access Token
CLOUDFLARE_TOKEN: Tunnel token
REGISTRY_USERNAME: Docker registry username
REGISTRY_PASSWORD: Docker registry password
``

**Add Secrets**:
``ash
# Via GitHub CLI
gh secret set GITHUB_TOKEN --body "___BEGIN___COMMAND_DONE_MARKER___$LASTEXITCODE(cat ~/.github/token)"
gh secret set CLOUDFLARE_TOKEN --body "___BEGIN___COMMAND_DONE_MARKER___$LASTEXITCODE(cat ~/.cloudflare/token)"

# Or manually in GitHub UI:
# Settings → Secrets and variables → Actions → New repository secret
``

#### Step 5b: Configure GitLab Variables (Optional)
**Required Variables**:
``yaml
GITLAB_TOKEN: Personal Access Token
REGISTRY_USERNAME: Registry credentials
REGISTRY_PASSWORD: Registry credentials
``

**Add Variables**:
``ash
# Via GitLab UI:
# Settings → CI/CD → Variables → Add variable

# Or via GitLab CLI:
gitlab variable create GITLAB_TOKEN --value "your-token"
``

---

### Phase 6: Testing & Verification

#### Step 6a: Test Domain Browsability
**Automated Test**:
``ash
./scripts/test-domains.sh

# Expected output:
✓ shopnoltd.dpdns.org: HTTP 200
✓ toolbox.shopnoltd.dpdns.org: HTTP 200
✓ grafana.shopnoltd.dpdns.org: HTTP 200
✓ argocd.shopnoltd.dpdns.org: HTTP 200
... (all 25+ domains)
``

**Manual Testing**:
``ash
# Test HTTPS connectivity
curl -I https://shopnoltd.dpdns.org
curl -I https://toolbox.shopnoltd.dpdns.org
curl -I https://grafana.shopnoltd.dpdns.org

# Expected: HTTP 200, 301 (redirect), or 503 (service not running yet)
# NOT: Connection refused, timeout, or ERR_NAME_NOT_RESOLVED
``

**Browser Testing**:
``
https://shopnoltd.dpdns.org
https://toolbox.shopnoltd.dpdns.org
https://grafana.shopnoltd.dpdns.org
https://argocd.shopnoltd.dpdns.org
``

#### Step 6b: Test Kubernetes Connectivity
``ash
# Verify ingress deployment
kubectl get ingress -a
# Expected: 9 ingress resources in various namespaces

# Verify services
kubectl get svc -a | grep -E "toolbox|erp|grafana|argocd"

# Verify Cloudflare Tunnel
kubectl logs -n kube-system -l app=cloudflared-global

# Verify Cert-Manager
kubectl logs -n cert-manager -l app=cert-manager
``

#### Step 6c: Test Auto-Sync
**GitHub Test**:
``ash
# Make a test commit
echo "test" >> test.txt
git add test.txt
git commit -m "test webhook"
git push origin main

# Check webhook server logs
sudo journalctl -u k8s-webhook -f

# Expected:
# [INFO] Received GitHub webhook
# [INFO] Syncing repository
# [SUCCESS] Auto-sync completed
``

**GitLab Test** (if configured):
``ash
# Push to GitLab
git push gitlab main

# Check logs
sudo journalctl -u k8s-webhook -f
``

---

## 🔄 Complete Deployment Flow

``
1. Prerequisites Verified ✓
   ↓
2. Git Repository Setup ✓
   ├─ GitHub Remote ✓
   └─ GitLab Remote (Optional)
   ↓
3. Kubernetes Cluster Started
   ├─ Namespaces created
   ├─ NGINX Ingress deployed
   ├─ Cert-Manager deployed
   └─ Cloudflare Tunnel connected
   ↓
4. DNS Configured ✓
   ├─ Root domain
   └─ 25+ subdomains
   ↓
5. Webhooks & Auto-Sync
   ├─ GitHub webhooks
   ├─ GitLab webhooks (Optional)
   └─ Webhook server running
   ↓
6. Secrets Configured
   ├─ GitHub secrets
   └─ GitLab variables (Optional)
   ↓
7. Testing & Verification
   ├─ Domain browsability tested
   ├─ K8s connectivity verified
   └─ Auto-sync functional
   ↓
✅ Platform Ready for Production
``

---

## 🆘 Troubleshooting

### DNS Resolution Issues
``ash
# Problem: Domains not resolving
# Solution:
nslookup shopnoltd.dpdns.org
dig shopnoltd.dpdns.org

# Check Cloudflare Tunnel
kubectl logs -n kube-system -l app=cloudflared-global
kubectl describe pod cloudflared-global -n kube-system
``

### Ingress Not Responding (502 Bad Gateway)
``ash
# Problem: Domains resolve but get 502 error
# Solution:
kubectl get svc -a
kubectl get pods -a
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Check if backend services exist
kubectl get svc -n toolbox
kubectl get svc -n erp
kubectl get svc -n monitoring
``

### Certificate Issues
``ash
# Problem: SSL certificate errors
# Solution:
kubectl get certificate -a
kubectl describe certificate -n toolbox toolbox-tls
kubectl logs -n cert-manager -l app=cert-manager

# Recreate certificate if stuck
kubectl delete certificate toolbox-tls -n toolbox
``

### Webhook Not Triggering
``ash
# Problem: Changes not syncing
# Solution:
sudo systemctl status k8s-webhook
sudo journalctl -u k8s-webhook -f
curl http://localhost:5000/health

# Check webhook delivery in GitHub/GitLab
# GitHub: Settings → Webhooks → Recent deliveries
# GitLab: Settings → Webhooks → Hooks
``

### Auto-Sync Failing
``ash
# Problem: Repository not syncing
# Solution:
kubectl get all -n argocd
kubectl logs -n argocd deployment/argocd-server
kubectl logs -n argocd deployment/argocd-repo-server

# Check git credentials
cat ~/.ssh/id_rsa
git remote -v
``

---

## 📊 Deployment Checklist

Copy this checklist and check off as you progress:

``
Phase 1: Git Setup
[ ] GitHub account configured
[ ] GitHub SSH keys set up
[ ] Repository cloned/forked
[ ] Git ownership fixed
[ ] GitHub remotes configured
[ ] GitLab remotes configured (optional)

Phase 2: Kubernetes
[ ] Cluster provisioned
[ ] kubectl configured
[ ] Cluster access verified
[ ] kubectl get nodes works

Phase 3: Infrastructure
[ ] NGINX Ingress deployed
[ ] Cert-Manager deployed
[ ] Cloudflare Tunnel running
[ ] ArgoCD deployed (optional)

Phase 4: Networking
[ ] DNS records verified
[ ] All 25+ domains resolving
[ ] Cloudflare Tunnel connected
[ ] Ingress routes active

Phase 5: Webhooks
[ ] Webhook server running
[ ] GitHub webhooks configured
[ ] GitLab webhooks configured (optional)
[ ] Webhook endpoints responding

Phase 6: Secrets
[ ] GitHub secrets set
[ ] GitLab variables set (optional)
[ ] SSH keys configured
[ ] Database credentials ready

Phase 7: Testing
[ ] Domains browsable via HTTP/HTTPS
[ ] All 25+ subdomains accessible
[ ] Webhook test successful
[ ] Auto-sync working
[ ] Certificate valid

Phase 8: Production Readiness
[ ] Monitoring configured
[ ] Alerts set up
[ ] Backup strategy ready
[ ] Documentation updated
[ ] Team trained
``

---

## 📞 Next Steps

After completing all phases:

1. **Deploy Applications**:
   ``ash
   # Deploy each application namespace
   kubectl apply -f apps/shopnoltd-toolbox/
   kubectl apply -f apps/erp/
   kubectl apply -f apps/monitoring/
   ``

2. **Configure Monitoring**:
   ``ash
   # Access monitoring dashboards
   https://grafana.shopnoltd.dpdns.org
   https://prometheus.shopnoltd.dpdns.org
   https://argocd.shopnoltd.dpdns.org
   ``

3. **Enable GitOps**:
   ``ash
   # Configure ArgoCD for automatic deployments
   argocd app create shopnoltd-platform
   argocd app set shopnoltd-platform --repo https://github.com/asaduzzamanbheramara-prog/k8s-platform
   ``

4. **Setup CI/CD**:
   ``ash
   # Configure GitHub Actions/GitLab CI
   # Push to deploy automatically
   ``

5. **Schedule Backups**:
   ``ash
   # Configure cluster backups
   # Setup disaster recovery
   ``

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [Cloudflare Tunnel Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [FreeDNS Documentation](https://freedns.afraid.org/)

---

## 📝 Document Information

**Version**: 1.0  
**Last Updated**: 2026-06-01  
**Status**: Complete  
**Maintained By**: Shopnoltd DevOps Team  
**Feedback**: Submit issues to the repository

---

*End of Setup Guide*
