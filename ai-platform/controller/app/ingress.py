import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
REGISTRY = BASE / "registry/domains.yaml"
OUT = BASE / "k8s/generated"

def load():
    return yaml.safe_load(open(REGISTRY))

def build(name, cfg):
    return f"""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}
  namespace: {cfg.get("namespace","default")}
spec:
  ingressClassName: traefik
  rules:
  - host: {cfg["host"]}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {cfg["service"]}
            port:
              number: {cfg["port"]}
"""

def run():
    OUT.mkdir(parents=True, exist_ok=True)

    data = load()

    for name, cfg in data["domains"].items():
        file = OUT / f"{name}.yaml"
        file.write_text(build(name, cfg))

    print("INGRESS GENERATED")

if __name__ == "__main__":
    run()
