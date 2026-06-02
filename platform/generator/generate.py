import yaml
from pathlib import Path

# =========================
# BASE PATHS
# =========================
BASE = Path(__file__).resolve().parents[1]

REGISTRY = BASE / "config/domain-registry.yaml"

# ONLY ONE SOURCE OF TRUTH FOR GITOPS
GITOPS_INGRESS = BASE / "gitops/ingress"
GITOPS_CLOUDFLARED = BASE / "gitops/cloudflared/cloudflared.yaml"


# =========================
# LOAD DOMAINS
# =========================
def load_domains():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)["domains"]


# =========================
# INGRESS TEMPLATE (FIXED)
# =========================
def build_ingress(name, host, service):
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}-ingress
  namespace: argocd
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web
spec:
  ingressClassName: traefik
  rules:
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {service}
            port:
              number: 80
"""
    

# =========================
# CLOUDFLARED TEMPLATE
# =========================
def cloudflared_header():
    return [
        "tunnel: cloudflared-global",
        "ingress:"
    ]


# =========================
# MAIN
# =========================
def main():
    domains = load_domains()

    # Ensure folders exist
    GITOPS_INGRESS.mkdir(parents=True, exist_ok=True)
    GITOPS_CLOUDFLARED.parent.mkdir(parents=True, exist_ok=True)

    cf = cloudflared_header()

    for name, cfg in domains.items():

        if not isinstance(cfg, dict):
            continue

        host = cfg.get("host")
        service = cfg.get("service", name)

        if not host:
            continue

        # ---------------------
        # INGRESS FILE
        # ---------------------
        ingress_file = GITOPS_INGRESS / f"{name}-ingress.yaml"

        ingress_file.write_text(
            build_ingress(name, host, service)
        )

        # ---------------------
        # CLOUDFLARED ROUTE
        # ALWAYS TRAEFIK
        # ---------------------
        cf.append(f"  - hostname: {host}")
        cf.append("    service: http://traefik.kube-system.svc.cluster.local:80")

    # fallback
    cf.append("  - service: http_status:404")

    GITOPS_CLOUDFLARED.write_text("\n".join(cf))

    print("✅ GitOps fully regenerated (stable + no drift)")


if __name__ == "__main__":
    main()
