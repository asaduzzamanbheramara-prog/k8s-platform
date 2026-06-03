import os
import requests

ZONE_ID = "bc13b09abb3f6b03ac725dc12a3cbac5"
TUNNEL_ID = "5d6e037a-7c09-4788-8532-11dba5fc1a72"

CF_TOKEN = os.getenv("CF_API_TOKEN")

BASE_URL = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"

HEADERS = {
    "Authorization": f"Bearer {CF_TOKEN}",
    "Content-Type": "application/json"
}


def get_record(name):
    """Check if DNS already exists"""
    r = requests.get(f"{BASE_URL}?name={name}", headers=HEADERS)
    data = r.json()

    if data.get("success") and data.get("result"):
        return data["result"][0]

    return None


def create_or_update_dns(host):
    print(f"[DNS] Processing {host}")

    existing = get_record(host)

    payload = {
        "type": "CNAME",
        "name": host,
        "content": f"{TUNNEL_ID}.cfargotunnel.com",
        "proxied": True,
        "ttl": 1
    }

    if existing:
        print(f"[SKIP] Already exists → {host}")
        return

    r = requests.post(BASE_URL, json=payload, headers=HEADERS)

    print(f"[CREATED] {host} →", r.json())
