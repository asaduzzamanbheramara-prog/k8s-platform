# Shopnoltd K8s Platform - Deployment Checklist

## ✅ Completed - Ingress Routes Created

The following ingress manifests have been created and are ready for deployment:

- [x] `gitops/ingress/root-ingress.yaml` - Root domain (shopnoltd.dpdns.org, www)
- [x] `gitops/ingress/kobo-ingress.yaml` - Kobo services (kf, kc, ee, kobo, kpi)
- [x] `gitops/ingress/erp-ingress.yaml` - ERP services (erp, billing, api)
- [x] `gitops/ingress/mail-ingress.yaml` - Mail service
- [x] `gitops/ingress/storage-ingress.yaml` - Storage service
- [x] `gitops/ingress/monitoring-ingress.yaml` - Monitoring (grafana, prometheus)
- [x] `gitops/ingress/portainer-ingress.yaml` - Portainer
- [x] `gitops/ingress/realtime-ingress.yaml` - Realtime services (chat, meet, live)
- [x] `gitops/ingress/argocd-ingress.yaml` - ArgoCD (already existed)
- [x] `gitops/ingress/kustomization.yaml` - Kustomization bundling all ingresses

## 🔧 Infrastructure Setup Required

Before ingress routes will work, you need:

### 1. Kubernetes Cluster ✓
- [ ] K3s or another Kubernetes distro installed
- [ ] `kubectl` configured and working
- [ ] At least 4GB RAM available

### 2. Core Services ✓
- [x] Namespaces created: `cluster/namespaces.yaml`
- [x] NGINX Ingress Controller: `cluster/ingress/nginx.yaml`
- [x] Cert-Manager: `cluster/addons/cert-manager.yaml`
- [x] Cloudflare Tunnel: `cluster/addons/cloudflared-global-deployment.yaml`
- [x] ArgoCD: `gitops/argocd/install.yaml`

### 3. Cloudflare Tunnel Setup ⚠️ REQUIRED
- [ ] Get Tunnel Token from https://dash.cloudflare.com/
- [ ] Create secret: `kubectl create secret generic cloudflared-global-secret -n kube-system --from-literal=TUNNEL_TOKEN='your_token'`
- [ ] Verify tunnel is running: `kubectl logs -n kube-system -l app=cloudflared-global`

### 4. DNS Records ✓
- [x] Already configured at FreeDNS for shopnoltd.dpdns.org
- [x] All subdomains routed via Cloudflare Tunnel

## 📦 Application Services - Need Implementation

These services must exist in their namespaces for traffic routing to work:

### kobo namespace
- [ ] **Service: kobocat** (port 8000)
  - Used by: kf.shopnoltd.dpdns.org, kc.shopnoltd.dpdns.org
  - Source: Create Deployment + Service for kobocat

- [ ] **Service: kpi** (port 8000)
  - Used by: ee.shopnoltd.dpdns.org, kobo.shopnoltd.dpdns.org, kpi.shopnoltd.dpdns.org
  - Source: Create Deployment + Service for KPI

### erp namespace
- [ ] **Service: erp-api** (port 8000)
  - Used by: erp.shopnoltd.dpdns.org, api.shopnoltd.dpdns.org
  - Source: Deploy ERP application

- [ ] **Service: billing-api** (port 8080)
  - Used by: billing.shopnoltd.dpdns.org
  - Source: Deploy Billing API

### mail namespace
- [ ] **Service: mail-service** (port 80)
  - Used by: mail.shopnoltd.dpdns.org
  - Source: Deploy Mail application

### storage namespace
- [ ] **Service: storage-service** (port 80)
  - Used by: storage.shopnoltd.dpdns.org
  - Source: Deploy Storage service

### monitoring namespace
- [ ] **Service: grafana** (port 3000)
  - Used by: grafana.shopnoltd.dpdns.org
  - Source: Deploy Grafana

- [ ] **Service: prometheus** (port 9090)
  - Used by: prometheus.shopnoltd.dpdns.org
  - Source: Deploy Prometheus

### portainer namespace
- [ ] **Service: portainer** (port 9000)
  - Used by: portainer.shopnoltd.dpdns.org
  - Source: Deploy Portainer

### realtime namespace
- [ ] **Service: chat-service** (port 3000)
  - Used by: chat.shopnoltd.dpdns.org
  - Source: Deploy Chat service

- [ ] **Service: meet-service** (port 8080)
  - Used by: meet.shopnoltd.dpdns.org
  - Source: Deploy Meet service

- [ ] **Service: live-service** (port 3000)
  - Used by: live.shopnoltd.dpdns.org
  - Source: Deploy Live streaming service

### argocd namespace
- [ ] **Service: root-app** (port 80)
  - Used by: shopnoltd.dpdns.org, www.shopnoltd.dpdns.org
  - Source: Create root application service

- [x] **Service: argocd-server** (port 80)
  - Used by: argocd.shopnoltd.dpdns.org
  - Already provided by: gitops/argocd/install.yaml

## 🚀 Deployment Steps

### Quick Start (Interactive)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Step-by-Step

```bash
# 1. Create namespaces
kubectl apply -f cluster/namespaces.yaml

# 2. Install cert-manager
kubectl apply -f cluster/addons/cert-manager.yaml
sleep 10

# 3. Install NGINX ingress
kubectl apply -f cluster/ingress/nginx.yaml
sleep 10

# 4. Setup Cloudflare tunnel
kubectl create secret generic cloudflared-global-secret \
  -n kube-system \
  --from-literal=TUNNEL_TOKEN='YOUR_TOKEN_HERE'

kubectl apply -f cluster/addons/cloudflared-global-deployment.yaml
kubectl apply -f cluster/addons/cloudflared-global/configmap.yaml

# 5. Install ArgoCD
kubectl apply -f gitops/argocd/install.yaml
sleep 10

# 6. Deploy ingress routes
kubectl apply -k gitops/ingress/

# 7. Verify deployment
kubectl get ingress -A
kubectl get pods -n ingress-nginx
kubectl get pods -n kube-system | grep cloudflared
kubectl logs -n kube-system -l app=cloudflared-global
```

## ✅ Verification

### Check Ingress Routes
```bash
kubectl get ingress -A
```

Expected output:
```
NAMESPACE     NAME                   CLASS   HOSTS                          ADDRESS   PORTS
argocd        argocd-ingress         nginx   argocd.shopnoltd.dpdns.org             80, 443
argocd        root-ingress           nginx   shopnoltd.dpdns.org, www...            80, 443
kobo          kobo-ingress           nginx   kf.shopnoltd.dpdns.org, ...            80, 443
erp           erp-ingress            nginx   erp.shopnoltd.dpdns.org, ...           80, 443
mail          mail-ingress           nginx   mail.shopnoltd.dpdns.org               80, 443
storage       storage-ingress        nginx   storage.shopnoltd.dpdns.org            80, 443
monitoring    monitoring-ingress     nginx   grafana.shopnoltd.dpdns.org, ...       80, 443
portainer     portainer-ingress      nginx   portainer.shopnoltd.dpdns.org          80, 443
realtime      realtime-ingress       nginx   chat.shopnoltd.dpdns.org, ...          80, 443
```

### Check Service Connectivity
```bash
# Test from a pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://ingress-nginx-controller.ingress-nginx.svc.cluster.local

# Expected: Should reach nginx-ingress service
```

### Check Tunnel Status
```bash
kubectl logs -n kube-system -l app=cloudflared-global -f

# Should show:
# - "Registered tunnel"
# - Route metrics
# - "Active connection"
```

## 🐛 Troubleshooting

### Issue: Domains return 404

**Cause**: Services don't exist in respective namespaces

**Solution**:
```bash
# Check available services
kubectl get svc -A

# Create missing services (if deploying test app):
kubectl create deployment test -n kobo --image=nginx
kubectl expose deployment test -n kobo --port=8000 --target-port=80
```

### Issue: 502 Bad Gateway

**Cause**: Service port mismatch or service not responding

**Solution**:
```bash
# Test service connectivity
kubectl port-forward -n kobo svc/kobocat 8000:8000
curl http://localhost:8000

# Check service endpoints
kubectl get endpoints -n kobo
```

### Issue: TLS certificate errors

**Cause**: Cert-manager not ready or Let's Encrypt not accessible

**Solution**:
```bash
# Check cert-manager pods
kubectl get pods -n cert-manager

# Describe certificate
kubectl describe cert -n kobo kobo-tls

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager -f
```

## 📚 Additional Resources

- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Full deployment documentation
- [Kubernetes Ingress Docs](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Cert-Manager Docs](https://cert-manager.io/docs/)
- [Cloudflared Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)

## 📝 Summary

**What's Ready**:
- ✅ DNS records (FreeDNS)
- ✅ Cloudflare Tunnel configuration
- ✅ NGINX Ingress routes (9 ingress manifests)
- ✅ TLS/SSL certificates (via cert-manager)
- ✅ Kustomization for all ingresses

**What's Next**:
1. Deploy cluster infrastructure (K3s, NGINX, cert-manager)
2. Configure Cloudflare Tunnel with your token
3. Create/deploy application services in respective namespaces
4. Test HTTPS access to each subdomain

Once all services are deployed, the platform will be **fully live** with secure HTTPS on all hostnames.
