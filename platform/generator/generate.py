#!/usr/bin/env python3

import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

REGISTRY = BASE / "config/domain-registry.yaml"
INGRESS_DIR = BASE / "generated/ingress"
CLOUDFLARED_FILE = BASE / "generated/cloudflared/cloudflared.yaml"


def load_registry():
    with open(REGISTRY, "r") as f:
        return yaml.safe_load(f)["domains"]


def flatten(domains):

    result = {}

    for key, value in domains.items():

        if not isinstance(value, dict):
            continue

        if "host" in value:
            result[key] = value
            continue

        for subkey, host in value.items():

            result[subkey] = {
                "host": host,
                "service": subkey
            }

    return result


def ingress_yaml(name, host, service):

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
            name: {service}-service
            port:
              number: 80
"""


def build_cloudflared(domains):

    lines = [
        "tunnel: cloudflared-global",
        "ingress:"
    ]

    for item in domains.values():

        lines.extend([
            f"  - hostname: {item['host']}",
            "    service: http://traefik.kube-system.svc.cluster.local:80"
        ])

    lines.append(
        "  - service: http_status:404"
    )

    return "\n".join(lines)


def main():

    INGRESS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CLOUDFLARED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    raw = load_registry()

    domains = flatten(raw)

    for old in INGRESS_DIR.glob("*.yaml"):
        old.unlink()

    for name, item in domains.items():

        host = item["host"]

        service = item.get(
            "service",
            name
        )

        output = (
            INGRESS_DIR /
            f"{name}-ingress.yaml"
        )

        output.write_text(
            ingress_yaml(
                name,
                host,
                service
            )
        )

    CLOUDFLARED_FILE.write_text(
        build_cloudflared(domains)
    )

    print(
        f"Generated {len(domains)} ingress resources"
    )

    print(
        f"Cloudflared config: {CLOUDFLARED_FILE}"
    )


if __name__ == "__main__":
    main()
