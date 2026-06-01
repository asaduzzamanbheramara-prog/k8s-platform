# Shopnoltd Platform - Domain & Subdomain Configuration

## Root Domain
**shopnoltd.dpdns.org** → Main Shopnoltd website

## Subdomains by Application

### Shopnoltd Toolbox (Survey Platform)
- toolbox.shopnoltd.dpdns.org → Main interface
- api.toolbox.shopnoltd.dpdns.org → API endpoint
- Legacy: kf, kc, kpi, ee (all redirect to toolbox)

### ERP System
- erp.shopnoltd.dpdns.org → Dashboard
- billing.shopnoltd.dpdns.org → Billing module
- api.erp.shopnoltd.dpdns.org → API

### Communication Services
- mail.shopnoltd.dpdns.org → Email service
- chat.shopnoltd.dpdns.org → Chat/Messaging
- meet.shopnoltd.dpdns.org → Video conferencing
- live.shopnoltd.dpdns.org → Live streaming

### Data & Storage
- storage.shopnoltd.dpdns.org → File storage (MinIO)
- db.shopnoltd.dpdns.org → Database access
- cache.shopnoltd.dpdns.org → Redis caching

### Monitoring & Management
- grafana.shopnoltd.dpdns.org → Metrics dashboard
- prometheus.shopnoltd.dpdns.org → Prometheus DB
- argocd.shopnoltd.dpdns.org → GitOps dashboard
- portainer.shopnoltd.dpdns.org → Container management

### AI & Development
- ai.shopnoltd.dpdns.org → AI service interface
- cursor.shopnoltd.dpdns.org → Code editor
- docs.shopnoltd.dpdns.org → Documentation

## Master Configuration
See config/domains.yaml for complete mapping and namespace assignments.
