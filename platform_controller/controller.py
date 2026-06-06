import os
import time
import yaml
import requests

from kubernetes import client
from kubernetes import config

REGISTRY_FILE = (
    "/app/app_platform/config/domain-registry.yaml"
)

CF_TOKEN = os.getenv("CF_API_TOKEN")
ZONE_ID = os.getenv("CF_ZONE_ID")
TUNNEL_ID = os.getenv("CF_TUNNEL_ID")

ZONE = "shopnoltd.dpdns.org"

HEADERS = {
    "Authorization": f"Bearer {CF_TOKEN}",
    "Content-Type": "application/json"
}

BASE_URL = (
    f"https://api.cloudflare.com/client/v4/"
    f"zones/{ZONE_ID}/dns_records"
)


def load_cluster():
    try:
        config.load_incluster_config()
    except Exception:
        config.load_kube_config()


def registry():
    with open(REGISTRY_FILE) as f:
        return yaml.safe_load(f)


def ensure_namespace(name):
    api = client.CoreV1Api()

    try:
        api.read_namespace(name)
        return
    except Exception:
        pass

    body = client.V1Namespace(
        metadata=client.V1ObjectMeta(name=name)
    )

    api.create_namespace(body)


def ensure_dns(host):
    url = f"{BASE_URL}?name={host}"

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    data = r.json()

    if data.get("result"):
        return

    payload = {
        "type": "CNAME",
        "name": host,
        "content":
            f"{TUNNEL_ID}.cfargotunnel.com",
        "proxied": True
    }

    requests.post(
        BASE_URL,
        headers=HEADERS,
        json=payload,
        timeout=30
    )


def reconcile():

    cfg = registry()

    domains = cfg.get("domains", {})

    for app, spec in domains.items():

        ns = spec["namespace"]
        host = spec["host"]

        ensure_namespace(ns)
        ensure_dns(host)

        print(
            f"OK {app} -> {host}"
        )


if __name__ == "__main__":

    load_cluster()

    while True:

        reconcile()

        time.sleep(300)
