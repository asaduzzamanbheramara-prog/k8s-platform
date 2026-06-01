import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REG = BASE / "config/domain-registry.yaml"
OUT = BASE / "gitops/cloudflared.yaml"

def load():
    return yaml.safe_load(open(REG))["domains"]

def main():
    d = load()

    lines = [
        "tunnel: cloudflared-global",
        "ingress:"
    ]

    for k, v in d.items():
        if isinstance(v, dict) and "host" in v:
            lines.append(f"  - hostname: {v['host']}")
            lines.append("    service: http://traefik.kube-system.svc.cluster.local:80")

    lines.append("  - service: http_status:404")

    OUT.write_text("\n".join(lines))
    print("✅ Cloudflared config regenerated")

if __name__ == "__main__":
    main()
