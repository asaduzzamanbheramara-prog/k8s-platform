import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent

REGISTRY = BASE / "config/domain-registry.yaml"
OUT = ROOT / "cluster/apps/ingress"

def load():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)

def build_ingress(name, cfg, settings):

    ingress_class = settings.get(
        "ingress_class",
        "traefik"
    )

    tls_secret = settings.get(
        "tls_secret"
    )

    namespace = cfg.get(
        "namespace",
        "default"
    )

    service = cfg["service"]

    port = cfg.get(
        "port",
        80
    )

    hosts = [cfg["host"]]
    hosts.extend(
        cfg.get("aliases", [])
    )

    rules = ""

    for host in hosts:
        rules += f"""
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {service}
            port:
              number: {port}
"""

    tls = ""

    if tls_secret:
        tls_hosts = "\n".join(
            [f"    - {h}" for h in hosts]
        )

        tls = f"""
  tls:
  - secretName: {tls_secret}
    hosts:
{tls_hosts}
"""

    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}
  namespace: {namespace}
spec:
  ingressClassName: {ingress_class}
{tls}
  rules:
{rules}
"""

def generate_kustomization(files):

    resources = "\n".join(
        [f"  - {f}" for f in files]
    )

    return f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
{resources}
"""

def main():

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    data = load()

    domains = data["domains"]
    settings = data["settings"]

    generated_files = []

    for name, cfg in domains.items():

        filename = f"{name}.yaml"

        ingress_file = OUT / filename

        ingress_file.write_text(
            build_ingress(
                name,
                cfg,
                settings
            )
        )

        generated_files.append(
            filename
        )

    kustomization = OUT / "kustomization.yaml"

    kustomization.write_text(
        generate_kustomization(
            generated_files
        )
    )

    print("OK GENERATED")

if __name__ == "__main__":
    main()
