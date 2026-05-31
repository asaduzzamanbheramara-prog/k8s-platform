# Shopnoltd K8s Platform - Deployment Guide

## Project Architecture Overview

This K8s platform uses a GitOps architecture with the following key components:

### Routing Layer (DNS → Tunnel → Ingress)
1. **DNS Records** (FreeDNS/Cloudflare)
   - All `*.shopnoltd.dpdns.org` records point to Cloudflare Tunnel

2. **Cloudflare Tunnel** (`cluster/addons/cloudflared-global/`)
   - Routes all hostnames to `ingress-nginx-controller` on port 80
   - Configured in: `configmap.yaml`, `deployment.yaml`
   - Tunnel token stored in: `kube-system/cloudflared-global-secret`

3. **NGINX Ingress Controller** (`cluster/ingress/`)
   - Deployed via Helm chart
   - Listens on all routes forwarded by tunnel
   - Routes traffic to backend services based on Ingress resources

### Ingress Resources (`gitops/ingress/`)

Ingress resources define hostname → service mappings:

| Hostname | Namespace | Service | Port |
|----------|-----------|---------|------|
| shopnoltd.dpdns.org, www | argocd | root-app | 80 |
| kf, kc, ee, kobo, kpi | kobo | kobocat/kpi | 8000 |
| erp, billing, api | erp | erp-api/billing-api | 8000/8080 |
| mail | mail | mail-service | 80 |
| storage | storage | storage-service | 80 |
| grafana, prometheus | monitoring | grafana/prometheus | 3000/9090 |
| portainer | portainer | portainer | 9000 |
| chat, meet, live | realtime | chat/meet/live services | 3000/8080 |
| argocd | argocd | argocd-server | 80 |

### Application Structure

Applications are deployed via ArgoCD Applications/ApplicationSets:
- `gitops/applications/` - Individual app manifests
- `gitops/appsets/` - ApplicationSet for dynamic app deployments
- `apps/` - Source paths for ArgoCD to sync (erp, mail, etc.)

### Namespace Organization

| Namespace | Purpose | Key Resources |
|-----------|---------|---|
| kube-system | System | Cloudflared tunnel, cert-manager |
| ingress-nginx | Ingress | NGINX controller |
| argocd | GitOps | ArgoCD server, ingress root-ingress.yaml |
| kobo | Data Collection | Kobocat (kf), KPI (kc/ee/kobo) |
| erp | Business Logic | ERP API, Billing API |
| mail | Messaging | Mail service |
| storage | Storage | File storage service |
| monitoring | Observability | Grafana, Prometheus |
| portainer | Container Mgmt | Portainer |
| realtime | Communication | Chat, Meet, Live services |

## Deployment Steps

### 1. Bootstrap Cluster

```bash
# Install K3s (if starting from scratch)
cd bootstrap
bash k3s-install.sh

# Create base namespaces
kubectl apply -f ../cluster/namespaces.yaml
```

### 2. Install Core Infrastructure

```bash
# Install cert-manager
kubectl apply -f cluster/addons/cert-manager.yaml

# Install ingress-nginx
kubectl apply -f cluster/ingress/nginx.yaml

# Install ArgoCD
kubectl apply -f gitops/argocd/install.yaml
```

### 3. Deploy Cloudflare Tunnel

```bash
# Create secret with your Cloudflare tunnel token
kubectl create secret generic cloudflared-global-secret \
  -n kube-system \
  --from-literal=TUNNEL_TOKEN='your_token_here'

# Deploy tunnel
kubectl apply -f cluster/addons/cloudflared-global-deployment.yaml
kubectl apply -f cluster/addons/cloudflared-global/configmap.yaml
```

> Note: `gitops/applications/cloudflared-global.yaml` contains a placeholder token by default. Do not commit a real tunnel token to source control; use the secret creation command above or a sealed secret mechanism.

### 4. Deploy Ingress Routes

```bash
# Apply all ingress resources
kubectl apply -k gitops/ingress/
```

### 5. Configure ArgoCD Applications

```bash
# Create platform project
kubectl apply -f gitops/projects/platform-project.yaml

# Deploy root application (syncs all apps)
kubectl apply -f gitops/root/root-app.yaml
```

### 6. Deploy Applications

ArgoCD will automatically sync these based on repository content:

```bash
# Optional: Manually trigger specific apps
kubectl apply -f gitops/applications/erp.yaml
kubectl apply -f gitops/applications/mail.yaml
kubectl apply -f gitops/applications/kobo.yaml
```

## DNS Configuration (FreeDNS)

All DNS records already configured at `shopnoltd.dpdns.org`:

- **Tunnel Records** (proxied via Cloudflare Tunnel):
  - shopnoltd.dpdns.org → cloudflared-global
  - *.shopnoltd.dpdns.org → cloudflared-global

- **Mail Records** (DNS only):
  - MX: smtp.shopnoltd.dpdns.org (priority 10)
  - SPF, DMARC, DKIM configured for Brevo

## TLS/SSL Certificates

All ingress resources use `cert-manager.io/cluster-issuer: letsencrypt-prod`:
- Certificates auto-generated per ingress rule
- Stored in secrets within respective namespaces
- Auto-renewed 30 days before expiry

## Service Configuration Requirements

For services to be accessible, they must exist in their respective namespaces:

### kobo namespace
- Service: `kobocat` (port 8000)
- Service: `kpi` (port 8000)

### erp namespace
- Service: `erp-api` (port 8000)
- Service: `billing-api` (port 8080)

### mail namespace
- Service: `mail-service` (port 80)

### storage namespace
- Service: `storage-service` (port 80)

### monitoring namespace
- Service: `grafana` (port 3000)
- Service: `prometheus` (port 9090)

### portainer namespace
- Service: `portainer` (port 9000)

### realtime namespace
- Service: `chat-service` (port 3000)
- Service: `meet-service` (port 8080)
- Service: `live-service` (port 3000)

### argocd namespace
- Service: `root-app` (port 80) - for root domain ingress
- Service: `argocd-server` (port 80) - for argocd subdomain

## Troubleshooting

### Domains not accessible

1. Check tunnel is running:
   ```bash
   kubectl logs -n kube-system -l app=cloudflared-global
   ```

2. Verify ingress exists:
   ```bash
   kubectl get ingress -A
   ```

3. Check NGINX controller:
   ```bash
   kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
   ```

4. Verify DNS:
   ```bash
   nslookup kf.shopnoltd.dpdns.org
   ```

### 502 Bad Gateway

- Backend service doesn't exist
- Service port mismatch in ingress
- Service not responding on expected port

Check:
```bash
kubectl get svc -A
kubectl get endpoints -A | grep service-name
kubectl port-forward -n namespace svc/service-name 8000:8000
```

### Certificate issues

```bash
kubectl get cert -A
kubectl describe cert -n namespace cert-name
```

## Quick Commands

```bash
# Watch ArgoCD syncing
kubectl get applications -A

# Check ingress status
kubectl get ingress -A -o wide

# Port-forward to debug
kubectl port-forward -n namespace svc/service-name local-port:remote-port

# View logs
kubectl logs -n namespace -l app=label-name -f

# Describe ingress route
kubectl describe ingress -n namespace ingress-name
```

## Next Steps

1. Ensure all required namespaces exist
2. Deploy respective applications in each namespace
3. Verify services are running and healthy
4. Test HTTPS accessibility on each subdomain
5. Configure monitoring and alerting
