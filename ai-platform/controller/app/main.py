import os
import yaml
import requests

CF_TOKEN = os.getenv("CF_API_TOKEN")
ZONE_ID = "bc13b09abb3f6b03ac725dc12a3cbac5"
TUNNEL = "5d6e037a-7c09-4788-8532-11dba5fc1a72"

REGISTRY = "/registry/domains.yaml"

def load():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)

def create_dns(host):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"

    payload = {
        "type": "CNAME",
        "name": host.split(".")[0],
        "content": f"{TUNNEL}.cfargotunnel.com",
        "proxied": True
    }

    headers = {
        "Authorization": f"Bearer {CF_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers)
    print(host, r.json())

def run():
    data = load()

    for name, cfg in data["domains"].items():
        create_dns(cfg["host"])

if __name__ == "__main__":
    run()
