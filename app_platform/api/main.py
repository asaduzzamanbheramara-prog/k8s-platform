from fastapi import FastAPI, Header, HTTPException
from pathlib import Path
import subprocess
import yaml

from app_platform.auth.auth import require_role

app = FastAPI()

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent

REGISTRY = BASE / "config/domain-registry.yaml"


def load():
    with open(REGISTRY) as f:
        return yaml.safe_load(f)


def save(data):
    with open(REGISTRY, "w") as f:
        yaml.dump(
            data,
            f,
            sort_keys=False
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/domains")
def domains(
    x_api_key: str = Header(None)
):
    if not require_role(
        x_api_key,
        ["admin", "developer", "viewer"]
    ):
        raise HTTPException(403)

    return load()


@app.post("/domain")
def add_domain(
    payload: dict,
    x_api_key: str = Header(None)
):
    if not require_role(
        x_api_key,
        ["admin", "developer"]
    ):
        raise HTTPException(403)

    data = load()

    name = payload["name"]

    data["domains"][name] = {
        "host": payload["host"],
        "aliases": payload.get(
            "aliases",
            []
        ),
        "service": payload.get(
            "service",
            name
        ),
        "namespace": payload.get(
            "namespace",
            "default"
        ),
        "port": payload.get(
            "port",
            80
        )
    }

    save(data)

    subprocess.run(
        [
            "python3",
            str(
                BASE /
                "generator/generate.py"
            )
        ],
        check=True
    )

    subprocess.run(
        [
            "git",
            "add",
            "."
        ],
        cwd=ROOT,
        check=True
    )

    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain"
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True
    )

    if status.stdout.strip():
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"add domain {name}"
            ],
            cwd=ROOT,
            check=True
        )

        subprocess.run(
            [
                "git",
                "push"
            ],
            cwd=ROOT,
            check=True
        )

    return {
        "ok": True,
        "domain": name
    }
