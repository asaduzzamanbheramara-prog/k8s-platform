import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REGISTRY = BASE / "config/domain-registry.yaml"
OUT = BASE / "gitops/ingress"

def load():
    return yaml.safe_load(open(REGISTRY))["domains"]

def template(name, host, service):
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}-ingress
  namespace: default
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
              number: 8000
"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load()

    for k, v in data.items():
        if not isinstance(v, dict):
            continue

        host = v.get("host")
        service = v.get("service", k)

        if host:
            (OUT / f"{k}-ingress.yaml").write_text(
                template(k, host, service)
            )

    print("✅ Ingress fully regenerated")

if __name__ == "__main__":
    main()
