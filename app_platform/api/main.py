from fastapi import FastAPI, Header, HTTPException
from pathlib import Path
import subprocess
import yaml
import os

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


def git_prepare():
    """
    Prepare git inside Kubernetes container.
    """

    subprocess.run(
        [
            "git",
            "config",
            "--global",
            "--add",
            "safe.directory",
            str(ROOT)
        ],
        check=False
    )

    subprocess.run(
        [
            "git",
            "config",
            "--global",
            "user.name",
            "Shopno Platform Bot"
        ],
        check=False
    )

    subprocess.run(
        [
            "git",
            "config",
            "--global",
            "user.email",
            "bot@shopnoltd.dpdns.org"
        ],
        check=False
    )

    token = os.getenv("GITHUB_TOKEN")

    if token:
        subprocess.run(
            [
                "git",
                "remote",
                "set-url",
                "origin",
                (
                    "https://"
                    f"{token}"
                    "@github.com/"
                    "asaduzzamanbheramara-prog/"
                    "k8s-platform.git"
                )
            ],
            cwd=ROOT,
            check=False
        )


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


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

    git_prepare()

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

        push = subprocess.run(
            [
                "git",
                "push"
            ],
            cwd=ROOT,
            capture_output=True,
            text=True
        )

        if push.returncode != 0:
            return {
                "ok": True,
                "domain": name,
                "warning": "git push failed",
                "stdout": push.stdout,
                "stderr": push.stderr
            }

    return {
        "ok": True,
        "domain": name
    }
