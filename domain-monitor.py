from fastapi import FastAPI
import requests
from kubernetes import client, config

app = FastAPI()

config.load_incluster_config()
v1 = client.NetworkingV1Api()

DOMAINS = []

def get_ingresses():
    ingresses = v1.list_ingress_for_all_namespaces().items
    result = []

    for ing in ingresses:
        if not ing.spec.rules:
            continue

        for rule in ing.spec.rules:
            host = rule.host
            url = f"http://{host}"

            status = "unknown"
            try:
                r = requests.get(url, timeout=3)
                status = str(r.status_code)
            except:
                status = "DOWN"

            result.append({
                "domain": host,
                "status": status,
                "url": url
            })

    return result


@app.get("/api/status")
def status():
    return get_ingresses()
