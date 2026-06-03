import os
import time
import requests

from kubernetes import client
from kubernetes import config
from kubernetes import watch

print("========== INGRESS DNS CONTROLLER ==========", flush=True)

CF_TOKEN = os.environ["CF_API_TOKEN"]
ZONE_ID = os.environ["CF_ZONE_ID"]
TUNNEL_ID = os.environ["CF_TUNNEL_ID"]

ZONE_NAME = "shopnoltd.dpdns.org"

BASE_URL = (
    f"https://api.cloudflare.com/client/v4/"
    f"zones/{ZONE_ID}/dns_records"
)

HEADERS = {
    "Authorization": f"Bearer {CF_TOKEN}",
    "Content-Type": "application/json",
}


def load_kube():
    try:
        config.load_incluster_config()
        print("Using in-cluster config", flush=True)
    except Exception:
        config.load_kube_config()
        print("Using local kubeconfig", flush=True)


def cf_request(method, url, **kwargs):

    r = requests.request(
        method,
        url,
        headers=HEADERS,
        timeout=30,
        **kwargs
    )

    print(
        f"[CF] {method} {url} -> {r.status_code}",
        flush=True
    )

    return r


def managed_host(host):

    return (
        host == ZONE_NAME
        or host.endswith("." + ZONE_NAME)
    )


def get_record(host):

    r = cf_request(
        "GET",
        f"{BASE_URL}?name={host}"
    )

    if r.status_code != 200:
        return None

    data = r.json()

    if not data.get("success"):
        return None

    result = data.get("result", [])

    if not result:
        return None

    return result[0]


def ensure_dns(host):

    if not managed_host(host):

        print(
            f"[SKIP] unmanaged host {host}",
            flush=True
        )

        return

    existing = get_record(host)

    if existing:

        print(
            f"[OK] DNS exists {host}",
            flush=True
        )

        return

    payload = {
        "type": "CNAME",
        "name": host,
        "content": f"{TUNNEL_ID}.cfargotunnel.com",
        "proxied": True,
        "ttl": 1
    }

    r = cf_request(
        "POST",
        BASE_URL,
        json=payload
    )

    data = r.json()

    if data.get("success"):

        print(
            f"[DNS CREATED] {host}",
            flush=True
        )

        return

    errors = data.get("errors", [])

    for err in errors:

        if err.get("code") == 81053:

            print(
                f"[SKIP] record already exists {host}",
                flush=True
            )

            return

    print(
        f"[DNS CREATE FAILED] {host}",
        flush=True
    )

    print(data, flush=True)


def remove_dns(host):

    if not managed_host(host):

        print(
            f"[SKIP] unmanaged host {host}",
            flush=True
        )

        return

    record = get_record(host)

    if not record:

        print(
            f"[OK] DNS already absent {host}",
            flush=True
        )

        return

    record_id = record["id"]

    r = cf_request(
        "DELETE",
        f"{BASE_URL}/{record_id}"
    )

    data = r.json()

    if data.get("success"):

        print(
            f"[DNS DELETED] {host}",
            flush=True
        )

        return

    print(
        f"[DNS DELETE FAILED] {host}",
        flush=True
    )

    print(data, flush=True)


def ingress_hosts(ingress):

    hosts = []

    if not ingress.spec:
        return hosts

    if not ingress.spec.rules:
        return hosts

    for rule in ingress.spec.rules:

        if rule.host:
            hosts.append(rule.host)

    return hosts


def reconcile(api):

    print(
        "Running reconciliation...",
        flush=True
    )

    count = 0

    ingresses = (
        api.list_ingress_for_all_namespaces()
        .items
    )

    for ingress in ingresses:

        for host in ingress_hosts(ingress):

            ensure_dns(host)
            count += 1

    print(
        f"Reconciled {count} hosts",
        flush=True
    )


def handle_event(event_type, ingress):

    hosts = ingress_hosts(ingress)

    for host in hosts:

        print(
            f"[EVENT] {event_type} -> {host}",
            flush=True
        )

        if event_type in ["ADDED", "MODIFIED"]:

            ensure_dns(host)

        elif event_type == "DELETED":

            remove_dns(host)


def run():

    load_kube()

    api = client.NetworkingV1Api()

    reconcile(api)

    while True:

        try:

            print(
                "Watching ingress resources...",
                flush=True
            )

            w = watch.Watch()

            for event in w.stream(
                api.list_ingress_for_all_namespaces,
                timeout_seconds=300
            ):

                handle_event(
                    event["type"],
                    event["object"]
                )

        except Exception as e:

            print(
                f"[WATCH ERROR] {e}",
                flush=True
            )

            time.sleep(5)

            try:
                reconcile(api)

            except Exception as ex:

                print(
                    f"[RECONCILE ERROR] {ex}",
                    flush=True
                )


if __name__ == "__main__":
    run()
