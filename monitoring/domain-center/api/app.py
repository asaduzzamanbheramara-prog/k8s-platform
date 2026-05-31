from fastapi import FastAPI
from kubernetes import client, config
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import requests
import socket
import time

app = FastAPI(
    title="Kubernetes Domain Monitor",
    version="4.0.0"
)

# --------------------------------------------------
# Kubernetes Config
# --------------------------------------------------

try:
    config.load_incluster_config()
    print("[INFO] Using in-cluster Kubernetes config")
except Exception:
    config.load_kube_config()
    print("[INFO] Using local kubeconfig")

networking = client.NetworkingV1Api()
core = client.CoreV1Api()

# --------------------------------------------------
# Domain Check
# --------------------------------------------------

def check_domain(host: str):

    result = {
        "domain": host,
        "timestamp": datetime.utcnow().isoformat(),
        "namespace": None,
        "ingress": None,
        "dns": False,
        "http": False,
        "https": False,
        "ssl": False,
        "resolved_ip": None,
        "status": "DOWN",
        "status_code": None,
        "response_time_ms": None,
        "redirected_url": None,
        "cloudflare_access": False,
        "error": None
    }

    if host.endswith(".local"):
        result["status"] = "INTERNAL"
        result["error"] = "local hostname"
        return result

    try:
        ip = socket.gethostbyname(host)
        result["dns"] = True
        result["resolved_ip"] = ip

    except Exception as e:
        result["error"] = f"DNS: {str(e)}"
        return result

    for scheme in ["https", "http"]:

        try:

            start = time.time()

            response = requests.get(
                f"{scheme}://{host}",
                timeout=(3, 5),
                allow_redirects=False,
                verify=True,
                headers={
                    "User-Agent": "ShopnoLtd-Domain-Monitor/4.0"
                }
            )

            elapsed = int(
                (time.time() - start) * 1000
            )

            result["status_code"] = response.status_code
            result["response_time_ms"] = elapsed

            if scheme == "https":
                result["https"] = True
                result["ssl"] = True
            else:
                result["http"] = True

            location = response.headers.get(
                "Location",
                ""
            )

            result["redirected_url"] = (
                location
                if location
                else f"{scheme}://{host}"
            )

            if "cloudflareaccess.com" in location:
                result["cloudflare_access"] = True
                result["status"] = "AUTH"
                return result

            if response.status_code in (
                200,
                201,
                202,
                204,
                301,
                302,
                307,
                308
            ):
                result["status"] = "UP"

            elif 400 <= response.status_code < 500:
                result["status"] = "WARNING"

            else:
                result["status"] = "DOWN"

            return result

        except requests.exceptions.SSLError as e:
            result["error"] = f"SSL: {str(e)}"

        except requests.exceptions.Timeout:
            result["error"] = "Timeout"

        except Exception as e:
            result["error"] = str(e)

    return result

# --------------------------------------------------
# Service Validation
# --------------------------------------------------

def service_exists(
    namespace: str,
    service_name: str
):

    try:

        core.read_namespaced_service(
            name=service_name,
            namespace=namespace
        )

        return True

    except Exception:

        return False

# --------------------------------------------------
# Ingress Discovery
# --------------------------------------------------

def get_all_hosts():

    hosts = []

    ingresses = (
        networking
        .list_ingress_for_all_namespaces()
        .items
    )

    print(
        f"[INFO] Found {len(ingresses)} ingresses"
    )

    for ingress in ingresses:

        namespace = ingress.metadata.namespace
        ingress_name = ingress.metadata.name

        ingress_class = (
            ingress.spec.ingress_class_name
        )

        if not ingress.spec.rules:
            continue

        for rule in ingress.spec.rules:

            host = rule.host

            if not host:
                continue

            backend_services = []
            missing_services = []

            if rule.http:

                for path in rule.http.paths:

                    if (
                        path.backend
                        and path.backend.service
                    ):

                        service_name = (
                            path.backend.service.name
                        )

                        backend_services.append(
                            service_name
                        )

                        if not service_exists(
                            namespace,
                            service_name
                        ):
                            missing_services.append(
                                service_name
                            )

            hosts.append({
                "host": host,
                "namespace": namespace,
                "ingress": ingress_name,
                "ingress_class": ingress_class,
                "backend_services": backend_services,
                "missing_services": missing_services
            })

    return hosts

# --------------------------------------------------
# Main Logic
# --------------------------------------------------

def get_ingresses():

    hosts = get_all_hosts()

    results = []

    with ThreadPoolExecutor(
        max_workers=20
    ) as executor:

        futures = {}

        for item in hosts:

            if item["missing_services"]:

                results.append({
                    "domain": item["host"],
                    "namespace": item["namespace"],
                    "ingress": item["ingress"],
                    "ingress_class": item["ingress_class"],
                    "backend_services": item["backend_services"],
                    "missing_services": item["missing_services"],
                    "status": "NO_SERVICE",
                    "error": (
                        "Missing services: "
                        + ", ".join(
                            item["missing_services"]
                        )
                    )
                })

                continue

            futures[
                executor.submit(
                    check_domain,
                    item["host"]
                )
            ] = item

        for future, item in futures.items():

            try:

                result = future.result()

                result["namespace"] = (
                    item["namespace"]
                )

                result["ingress"] = (
                    item["ingress"]
                )

                result["ingress_class"] = (
                    item["ingress_class"]
                )

                result["backend_services"] = (
                    item["backend_services"]
                )

                results.append(result)

            except Exception as e:

                results.append({
                    "domain": item["host"],
                    "namespace": item["namespace"],
                    "ingress": item["ingress"],
                    "status": "DOWN",
                    "error": str(e)
                })

    results.sort(
        key=lambda x: x.get(
            "domain",
            ""
        )
    )

    return results

@app.get("/")
def root():

    return {
        "service": "ShopnoLtd Kubernetes Domain Monitor",
        "version": "4.0.0",
        "status": "running"
    }

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
def api_status():

    return get_ingresses()

@app.get("/api/summary")
def api_summary():

    results = get_ingresses()

    total = len(results)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": total,
        "up": len([x for x in results if x["status"] == "UP"]),
        "down": len([x for x in results if x["status"] == "DOWN"]),
        "warning": len([x for x in results if x["status"] == "WARNING"]),
        "auth": len([x for x in results if x["status"] == "AUTH"]),
        "internal": len([x for x in results if x["status"] == "INTERNAL"]),
        "no_service": len([x for x in results if x["status"] == "NO_SERVICE"]),
        "success_rate": round(
            (
                len(
                    [x for x in results if x["status"] == "UP"]
                ) / total
            ) * 100,
            2
        ) if total else 0
    }
