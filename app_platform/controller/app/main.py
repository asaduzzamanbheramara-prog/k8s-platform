from fastapi import FastAPI, Header, HTTPException, Request
import yaml
import os
import subprocess
import time

app = FastAPI(title="SaaS Domain Control Plane (Production)")

# -----------------------------
# CONFIG
# -----------------------------
REGISTRY_PATH = "/home/shopno/k8s-platform/config/domains.yaml"
API_KEY = os.getenv("DOMAIN_API_KEY")

CRONJOB_NAME = "ingress-dns-sync"
NAMESPACE = "default"


# -----------------------------
# AUTH (FIXED - MANUAL HEADER READ)
# -----------------------------
def auth(request: Request):
    x_api_key = request.headers.get("x-api-key")

    if not API_KEY:
        raise HTTPException(500, "API KEY missing in environment")

    if not x_api_key:
        raise HTTPException(403, "Missing API key")

    if x_api_key != API_KEY:
        raise HTTPException(403, "Forbidden")


# -----------------------------
# REGISTRY
# -----------------------------
def load_registry():
    try:
        with open(REGISTRY_PATH, "r") as f:
            return yaml.safe_load(f) or {"domains": {}}
    except FileNotFoundError:
        return {"domains": {}}


def save_registry(data):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        yaml.safe_dump(data, f)


# -----------------------------
# SYNC ENGINE
# -----------------------------
def trigger_full_sync():
    job_name = f"manual-sync-{int(time.time())}"

    result = subprocess.run(
        [
            "kubectl",
            "create",
            "job",
            "--from=cronjob/" + CRONJOB_NAME,
            job_name,
            "-n",
            NAMESPACE,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("[SYNC ERROR]", result.stderr)
        return False

    print("[SYNC TRIGGERED]", job_name)
    return True


# -----------------------------
# HEALTH
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "domain-saas"}


# -----------------------------
# GET DOMAINS
# -----------------------------
@app.get("/domains")
def get_domains(request: Request):
    auth(request)
    return load_registry()


# -----------------------------
# ADD DOMAIN
# -----------------------------
@app.post("/domain")
def add_domain(payload: dict, request: Request):
    auth(request)

    if "name" not in payload or "host" not in payload:
        raise HTTPException(400, "name and host required")

    data = load_registry()

    if "domains" not in data:
        data["domains"] = {}

    name = payload["name"]
    data["domains"][name] = payload

    save_registry(data)

    trigger_full_sync()

    return {
        "status": "created",
        "name": name,
        "host": payload["host"]
    }


# -----------------------------
# DELETE DOMAIN
# -----------------------------
@app.delete("/domain/{name}")
def delete_domain(name: str, request: Request):
    auth(request)

    data = load_registry()

    if name not in data.get("domains", {}):
        raise HTTPException(404, "Domain not found")

    host = data["domains"][name]["host"]

    del data["domains"][name]
    save_registry(data)

    trigger_full_sync()

    return {
        "status": "deleted",
        "name": name,
        "host": host
    }
