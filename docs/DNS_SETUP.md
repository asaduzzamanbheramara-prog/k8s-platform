# DNS Configuration for Shopnoltd K8s Platform

## Overview
This document details the DNS setup for the Shopnoltd K8s platform.

## Root Domain & Provider

- **Root Domain**: shopnoltd.dpdns.org
- **DNS Provider**: FreeDNS (dpdns.org)
- **SSL**: Cloudflare Universal SSL (Free)

## Current DNS Records (19 Total)

All configured in Cloudflare with CNAME to cloudflared-global tunnel.

**Tunnel ID**: 5d6e037a-7c09-4788-8532-11dba5fc1a72.cfargotunnel.com

### ShopnoltdToolbox Services (Legacy)
- kf.shopnoltd.dpdns.org
- kc.shopnoltd.dpdns.org
- kpi.shopnoltd.dpdns.org
- ee.shopnoltd.dpdns.org
- kobo.shopnoltd.dpdns.org

### Toolbox (Modern)
- toolbox.shopnoltd.dpdns.org
- api.toolbox.shopnoltd.dpdns.org

### ERP System
- erp.shopnoltd.dpdns.org
- billing.shopnoltd.dpdns.org
- api.erp.shopnoltd.dpdns.org

### Communication Services
- mail.shopnoltd.dpdns.org
- chat.shopnoltd.dpdns.org
- meet.shopnoltd.dpdns.org
- live.shopnoltd.dpdns.org

### Data & Storage
- storage.shopnoltd.dpdns.org
- db.shopnoltd.dpdns.org
- cache.shopnoltd.dpdns.org

### Monitoring & Management
- grafana.shopnoltd.dpdns.org
- prometheus.shopnoltd.dpdns.org
- argocd.shopnoltd.dpdns.org
- portainer.shopnoltd.dpdns.org

### AI & Development
- ai.shopnoltd.dpdns.org
- cursor.shopnoltd.dpdns.org
- docs.shopnoltd.dpdns.org

### Root & General
- shopnoltd.dpdns.org
- www.shopnoltd.dpdns.org
- api.shopnoltd.dpdns.org

## Cloudflare Tunnel Setup

### Configuration
- **Tunnel Name**: cloudflared-global
- **Tunnel ID**: 5d6e037a-7c09-4788-8532-11dba5fc1a72
- **Status**: Active (4 connections)
- **Security**: Universal SSL, HTTP/2, DDoS Protection

## Adding New Subdomains

### Step 1: Add to FreeDNS
1. Log in to https://freedns.afraid.org/
2. Domains -> Manage Domains -> Add Domain
3. Enter: newservice.shopnoltd.dpdns.org
4. Save

### Step 2: Add to Cloudflare DNS
1. Cloudflare Dashboard -> DNS -> Records -> Add Record
2. Type: CNAME
3. Name: newservice
4. Target: 5d6e037a-7c09-4788-8532-11dba5fc1a72.cfargotunnel.com
5. Proxy: Proxied (Orange Cloud)
6. Save

### Step 3: Add Ingress Rule
Edit k8s/ingress/main-ingress.yaml and add:
`yaml
  - host: newservice.shopnoltd.dpdns.org
    http:
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: newservice-service
              port:
                number: 80
`

Apply:
`ash
kubectl apply -f k8s/ingress/main-ingress.yaml
`

### Step 4: Test DNS Resolution
`ash
dig newservice.shopnoltd.dpdns.org
nslookup newservice.shopnoltd.dpdns.org
curl -I https://newservice.shopnoltd.dpdns.org
`

## Testing DNS Health

### Quick Health Check
`ash
bash /home/shopno/k8s-platform/check-domains.sh
`

### Manual Tests
`ash
# Test DNS resolution
dig @1.1.1.1 kf.shopnoltd.dpdns.org

# Check CNAME chain
dig +trace kf.shopnoltd.dpdns.org

# Test HTTPS
curl -I https://kf.shopnoltd.dpdns.org

# Check certificate
openssl s_client -connect kf.shopnoltd.dpdns.org:443 -servername kf.shopnoltd.dpdns.org

# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info cloudflared-global
`

## DNS Troubleshooting

### Domain not resolving
- Verify FreeDNS record exists
- Check Cloudflare DNS record is proxied (orange cloud)
- Wait 5-10 minutes for propagation
- Clear DNS cache: sudo systemctl restart systemd-resolved

### SSL certificate error
- Verify domain is proxied in Cloudflare
- Check Cloudflare SSL/TLS -> Edge Certificates
- Wait for automatic issuance (up to 15 minutes)

### 502 Bad Gateway
- Check tunnel: cloudflared tunnel info
- Verify ingress routes: kubectl get ingress -A
- Check service status: kubectl get svc -A

### Tunnel down/disconnected
`ash
sudo systemctl restart cloudflared
docker restart cloudflared-tunnel
cloudflared tunnel status
`

## DNS Configuration Files

### Reference Files
- docs/DOMAINS.md - High-level domain mapping
- docs/KOBOTOOLBOX_DOMAINS.md - Service-specific configuration
- k8s/ingress/main-ingress.yaml - Kubernetes routing
- config/domains.yaml - Master domain mapping
- scripts/check-domains.sh - Automated verification

## Backup & Recovery

### Backup DNS Records
`ash
curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer {api_token}" | jq . > dns_backup.json
`

### Recovery
1. Tunnel down: Restart cloudflared service
2. DNS records deleted: Restore from backup
3. Nameservers changed: Verify FreeDNS points to Cloudflare

## Important Notes

- SSL Certificates: Managed by Cloudflare (automatic renewal)
- DNS Propagation: 5-10 minutes globally
- Monitoring: Run health check weekly
- Subdomain Limit: Unlimited on FreeDNS
- Tunnel Bandwidth: Included with Cloudflare free tier
- Security: All traffic encrypted end-to-end through tunnel

## References
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- FreeDNS: https://freedns.afraid.org/
- Kubernetes Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
