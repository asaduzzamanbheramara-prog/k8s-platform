# Shopnoltd K8s Platform - Architecture Documentation

## Overview

This document describes the architectural design of the Shopnoltd Kubernetes platform, including infrastructure, networking, and application topology.

## System Architecture

\\\
┌─────────────────────────────────────────────────────────────┐
│                    Internet (HTTPS)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│          Cloudflare Tunnel (cloudflared)                    │
│   DNS: shopnoltd.dpdns.org → Tunnel Endpoint               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│       NGINX Ingress Controller                              │
│   - HTTP/2 Support                                          │
│   - WebSocket Support                                       │
│   - TLS Termination                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌────────┐      ┌────────┐      ┌────────┐
   │Ingress │      │Ingress │      │Ingress │
   │Routes  │      │Routes  │      │Routes  │
   └────┬───┘      └────┬───┘      └────┬───┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────────────────┐
        │                │                            │
        ▼                ▼                            ▼
   ┌──────────┐    ┌──────────┐                ┌──────────┐
   │Toolbox   │    │ERP       │    ... Others  │Storage   │
   │Services  │    │Services  │                │Services  │
   └──────────┘    └──────────┘                └──────────┘
        │                │                            │
        ▼                ▼                            ▼
   ┌──────────┐    ┌──────────┐                ┌──────────┐
   │Pods      │    │Pods      │                │Pods      │
   │(Toolbox  │    │(ERP      │                │(Storage) │
   │ Frontend)│    │ Backend) │                └──────────┘
   └──────────┘    └──────────┘
\\\

## Directory Structure

\\\
k8s-platform/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # This file
│   ├── DEPLOYMENT_GUIDE.md        # Deployment instructions
│   ├── DEPLOYMENT_CHECKLIST.md    # Operational checklist
│   └── KOBOTOOLBOX_DOMAINS.md     # Legacy domain docs
│
├── scripts/                       # Deployment and utility scripts
│   ├── deploy.sh                  # Automated deployment
│   ├── sync.sh                    # Repository sync
│   ├── backup.sh                  # Backup procedures
│   ├── health-check.sh            # Health monitoring
│   └── domain-monitor.py          # Domain monitoring
│
├── config/                        # Centralized configurations
│   ├── domains.yaml               # Domain and subdomain mapping (MASTER)
│   ├── namespaces.yaml            # Kubernetes namespaces
│   ├── clusterissuer.yaml         # Cert-manager cluster issuer
│   └── db-init.yaml               # Database initialization
│
├── infrastructure/                # Core K8s infrastructure
│   ├── certificates/              # TLS certificates
│   ├── networking/                # Network policies
│   ├── rbac/                      # Role-based access control
│   └── storage/                   # Persistent storage config
│
├── apps/                          # Application manifests
│   ├── shopnoltd-toolbox/         # Toolbox App (Formerly ShopnoltdToolbox)
│   │   ├── base/
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   └── prod/
│   │   └── kustomization.yaml
│   │
│   ├── erp/                       # ERP System
│   │   ├── base/
│   │   └── kustomization.yaml
│   │
│   ├── realtime/                  # Real-time Services
│   │   ├── chat/
│   │   ├── meet/
│   │   ├── live/
│   │   └── kustomization.yaml
│   │
│   ├── mail/                      # Email Services
│   ├── storage/                   # File Storage
│   ├── monitoring/                # Monitoring & Observability
│   ├── openai/                    # AI Services
│   ├── cursor/                    # Development Tools
│   ├── queue/                     # Message Queue
│   └── root.yaml                  # ArgoCD root application
│
├── gitops/                        # ArgoCD Configurations
│   ├── applications/              # Application resources
│   ├── appsets/                   # ApplicationSets
│   ├── ingress/                   # Ingress resources
│   ├── projects/                  # ArgoCD projects
│   ├── argocd/                    # ArgoCD configuration
│   └── root.yaml                  # ArgoCD bootstrap
│
├── platform/                      # Platform-level configurations
│   ├── certificates/              # Certificate configurations
│   └── rbac/                      # RBAC configurations
│
├── docker/                        # Docker-related files
│   └── Dockerfile                 # Main container image
│
├── backup/                        # Archived/backup files
│   ├── kobocat-*.yaml             # Legacy KoboCAT configs
│   ├── kpi-configmap-backup.yaml  # Legacy KPI configs
│   └── cloudflared-backup.yaml    # Backup tunnels
│
├── k8s/                           # Raw Kubernetes manifests
│   ├── SAMPLE_SERVICES.yaml       # Service templates
│   └── argocd-root.yaml           # ArgoCD bootstrap
│
└── cluster/                       # Cluster configuration
    ├── bootstrap/
    └── monitoring/
\\\

## Namespaces

All applications run in isolated namespaces:

| Namespace | Applications | Purpose |
|-----------|--------------|---------|
| \	oolbox\ | KPI, KoboCAT, Toolbox Frontend | Survey management |
| \rp\ | ERP App, Billing, API | Business operations |
| \communication\ | Mail, Chat, Meet, Live | Communication services |
| \storage\ | MinIO, Backup Services | Data storage |
| \monitoring\ | Grafana, Prometheus, ArgoCD | Observability |
| \i\ | OpenAI Services | AI/ML integration |
| \ealtime\ | Real-time Hub | Event-driven services |
| \development\ | Cursor, Tools | Development environment |
| \queue\ | Message Brokers | Queue systems |
| \mail\ | Mail Services | Email handling |

## Domain Routing

All subdomains route through:

1. **External DNS** → FreeDNS (shopnoltd.dpdns.org)
2. **DNS Records** → Cloudflare Tunnel endpoint
3. **Tunnel** → Cloudflared service in kube-system
4. **Ingress Controller** → NGINX ingress in ingress-nginx
5. **Ingress Routes** → Services in respective namespaces

See \config/domains.yaml\ for complete subdomain mapping.

## TLS/SSL Certificate Management

- **Issuer**: Let's Encrypt (Production)
- **Manager**: Cert-manager
- **Validation**: ACME HTTP-01 challenge
- **Wildcard Certificate**: shopnoltd.dpdns.org and *.shopnoltd.dpdns.org
- **Auto-renewal**: 30 days before expiration

## Storage Architecture

- **Persistent Volumes**: Local storage or cloud backend
- **Storage Classes**: Standard, Fast, Archive tiers
- **Database**: PostgreSQL (toolbox, ERP data)
- **Object Storage**: MinIO (S3-compatible)
- **Cache**: Redis

## Security Layers

1. **Network Layer**: Network policies, firewalls
2. **TLS/SSL**: Encrypted communication (HTTPS/WSS)
3. **Authentication**: Service accounts, RBAC
4. **Secrets Management**: Kubernetes Secrets or Vault
5. **RBAC**: Role-based access control per namespace

## Monitoring & Observability

- **Metrics**: Prometheus scrapes all services
- **Dashboards**: Grafana visualizations
- **Logs**: Centralized logging (ELK or similar)
- **Health Checks**: Regular endpoint monitoring
- **Alerts**: Prometheus AlertManager

## Disaster Recovery

- **Backup**: Automated daily backups
- **Recovery**: Backup restoration procedures in \scripts/restore.sh\
- **RPO**: < 24 hours
- **RTO**: < 1 hour
- **Test Schedule**: Monthly backup restore tests

## Performance Optimization

- **CDN**: Cloudflare CDN for static assets
- **Caching**: Redis layer for frequently accessed data
- **Load Balancing**: NGINX ingress load balancing
- **Auto-scaling**: HPA for dynamic workloads
- **Resource Limits**: CPU and memory quotas per namespace

## Maintenance & Operations

- **Updates**: ArgoCD GitOps workflow for deployments
- **Scaling**: Manual or automatic scaling policies
- **Patching**: Kubernetes and application patches
- **Compliance**: Regular security audits
- **Monitoring**: 24/7 monitoring and alerting
