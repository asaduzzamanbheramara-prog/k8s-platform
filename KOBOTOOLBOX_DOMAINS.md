# KoboToolbox Configuration for Shopnoltd Platform

## Environment Variables for KoboToolbox Services

Update the following files with all domains and subdomains:

### 1. KOBOCAT Configuration (apps/kobo/kobocat.yaml)

```yaml
env:
  - name: ALLOWED_HOSTS
    value: "kf.shopnoltd.dpdns.org,kc.shopnoltd.dpdns.org,kobocat.shopnoltd.dpdns.org,shopnoltd.dpdns.org,www.shopnoltd.dpdns.org"
  
  - name: KPI_URL
    value: "https://kpi.shopnoltd.dpdns.org"
  
  - name: KOBO_URL
    value: "https://kf.shopnoltd.dpdns.org"
  
  - name: KOBOCAT_URL
    value: "https://kc.shopnoltd.dpdns.org"
  
  - name: CSRF_COOKIE_SECURE
    value: "true"
  
  - name: SESSION_COOKIE_SECURE
    value: "true"
  
  - name: SECURE_SSL_REDIRECT
    value: "true"
```

### 2. KPI Configuration (apps/kobo/kpi.yaml)

```yaml
env:
  - name: ALLOWED_HOSTS
    value: "kpi.shopnoltd.dpdns.org,kobo.shopnoltd.dpdns.org,ee.shopnoltd.dpdns.org,shopnoltd.dpdns.org,www.shopnoltd.dpdns.org"
  
  - name: KOBOCAT_URL
    value: "https://kc.shopnoltd.dpdns.org"
  
  - name: KOBO_URL
    value: "https://kf.shopnoltd.dpdns.org"
  
  - name: KPI_URL
    value: "https://kpi.shopnoltd.dpdns.org"
  
  - name: CSRF_COOKIE_SECURE
    value: "true"
  
  - name: SESSION_COOKIE_SECURE
    value: "true"
  
  - name: SECURE_SSL_REDIRECT
    value: "true"
  
  - name: CSRF_TRUSTED_ORIGINS
    value: "https://kpi.shopnoltd.dpdns.org,https://kf.shopnoltd.dpdns.org,https://kc.shopnoltd.dpdns.org,https://shopnoltd.dpdns.org,https://www.shopnoltd.dpdns.org"
```

## All Domains & Subdomains Available

### KoboToolbox Services
| Subdomain | Service | Purpose |
|-----------|---------|---------|
| `kf.shopnoltd.dpdns.org` | KoboForm | Primary Kobo Forms interface |
| `kc.shopnoltd.dpdns.org` | KoboCat | Backend Kobo service |
| `kobo.shopnoltd.dpdns.org` | Kobo (alternate) | Alternate entry point |
| `kpi.shopnoltd.dpdns.org` | KPI Module | Key Performance Indicators |
| `ee.shopnoltd.dpdns.org` | Entity Editor | Entity editing interface |

### ERP Services
| Subdomain | Service | Purpose |
|-----------|---------|---------|
| `erp.shopnoltd.dpdns.org` | ERP Main | Main ERP interface |
| `billing.shopnoltd.dpdns.org` | Billing API | Billing operations |
| `api.shopnoltd.dpdns.org` | API Gateway | API endpoint |

### Monitoring & Operations
| Subdomain | Service | Purpose |
|-----------|---------|---------|
| `grafana.shopnoltd.dpdns.org` | Grafana | Monitoring dashboards |
| `prometheus.shopnoltd.dpdns.org` | Prometheus | Metrics collection |
| `portainer.shopnoltd.dpdns.org` | Portainer | Container management |
| `argocd.shopnoltd.dpdns.org` | ArgoCD | GitOps deployment |

### Communication Services
| Subdomain | Service | Purpose |
|-----------|---------|---------|
| `mail.shopnoltd.dpdns.org` | Mail Service | Email operations |
| `chat.shopnoltd.dpdns.org` | Chat | Real-time messaging |
| `meet.shopnoltd.dpdns.org` | Meet | Video conferencing |
| `live.shopnoltd.dpdns.org` | Live Stream | Live streaming |

### Storage & Root
| Domain | Service | Purpose |
|--------|---------|---------|
| `shopnoltd.dpdns.org` | Root | Main domain |
| `www.shopnoltd.dpdns.org` | WWW | WWW alias |
| `storage.shopnoltd.dpdns.org` | Storage | File storage |

## How to Apply Configuration

### Option 1: Using Secrets (Recommended)

```bash
kubectl create secret generic kobo-domains \
  --from-literal=ALLOWED_HOSTS="kf.shopnoltd.dpdns.org,kc.shopnoltd.dpdns.org,kobo.shopnoltd.dpdns.org,shopnoltd.dpdns.org" \
  --from-literal=KPI_URL="https://kpi.shopnoltd.dpdns.org" \
  -n kobo
```

### Option 2: Using ConfigMap

```bash
kubectl create configmap kobo-config \
  --from-literal=ALLOWED_HOSTS="kf.shopnoltd.dpdns.org,kc.shopnoltd.dpdns.org,kobo.shopnoltd.dpdns.org,shopnoltd.dpdns.org" \
  --from-literal=KPI_URL="https://kpi.shopnoltd.dpdns.org" \
  -n kobo
```

## DNS Records Summary

All 19 domains/subdomains are configured in Cloudflare:
- **Root Domain**: shopnoltd.dpdns.org
- **Tunnel**: cloudflared-global (4 active connections)
- **DNS Type**: CNAME → 5d6e037a-7c09-4788-8532-11dba5fc1a72.cfargotunnel.com
- **Status**: All Proxied & Active ✅

## Verification

Run the health check:
```bash
bash /home/shopno/k8s-platform/check-domains.sh
```

Expected output:
- All domains responding with HTTP 2xx, 3xx, or 302 (redirects)
- Tunnel status: Active
- Ingress routes: 9 deployed
