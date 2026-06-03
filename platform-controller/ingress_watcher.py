from kubernetes import client, config
import requests
import os

CF_TOKEN = os.getenv("CF_API_TOKEN")
ZONE_ID = os.getenv("CF_ZONE_ID")
TUNNEL_ID = os.getenv("CF_TUNNEL_ID")

HEADERS = {
    "Authorization": f"Bearer {CF_TOKEN}",
    "Content-Type": "application/json"
}

BASE = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"


def create_dns(host):
    # Get ALL records (reliable way)
    existing = requests.get(BASE, headers=HEADERS).json()

    for record in existing.get("result", []):
        if record.get("name") == host:
            print("[SKIP] already exists:", host)
            return

    payload = {
        "type": "CNAME",
        "name": host,
        "content": f"{TUNNEL_ID}.cfargotunnel.com",
        "proxied": True,
        "ttl": 1
    }

    r = requests.post(BASE, json=payload, headers=HEADERS)
    print("[DNS SYNC]", host, r.json())


def load_kube():
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()


def get_ingresses():
    load_kube()
    v1 = client.NetworkingV1Api()
    return v1.list_ingress_for_all_namespaces().items


def run():
    print("🚀 Syncing Ingress → Cloudflare DNS...")

    ingresses = get_ingresses()

    for ing in ingresses:
        if not ing.spec or not ing.spec.rules:
            continue

        for rule in ing.spec.rules:
            host = rule.host
            print(f"➡ Found: {host}")
            create_dns(host)

    print("✅ DNS Sync Completed")


if __name__ == "__main__":
    run()
