import yaml
import subprocess
from pathlib import Path

ROOT = Path.home() / "k8s-platform"

REGISTRY = ROOT / "config/domain-registry.yaml"
TEMPLATES = ROOT / "config/app-templates.yaml"


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False
        )


def ensure_freedomain():

    repo = Path.home() / "FreeDomain"

    if not repo.exists():

        subprocess.run(
            [
                "git",
                "clone",
                "https://github.com/DigitalPlatDev/FreeDomain.git",
                str(repo)
            ],
            check=True
        )

    else:

        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "pull"
            ],
            check=True
        )

    return repo


def register_domain(name):

    ensure_freedomain()

    return f"{name}.shopnoltd.dpdns.org"


def add_app(name, template):

    templates = load_yaml(TEMPLATES)
    registry = load_yaml(REGISTRY)

    if template not in templates["templates"]:
        raise Exception(
            f"Template '{template}' not found"
        )

    if "domains" not in registry:
        registry["domains"] = {}

    if name in registry["domains"]:
        raise Exception(
            f"Domain '{name}' already exists"
        )

    spec = templates["templates"][template]

    registry["domains"][name] = {
        "namespace": name,
        "host": register_domain(name),
        "image": spec["image"],
        "port": spec["port"]
    }

    save_yaml(REGISTRY, registry)

    print()
    print("Created:")
    print(name)
    print(registry["domains"][name]["host"])


def generate():

    subprocess.run(
        [
            "python3",
            "platform_controller/generator.py"
        ],
        cwd=ROOT,
        check=True
    )


def git_push():

    subprocess.run(
        ["git", "add", "."],
        cwd=ROOT,
        check=True
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "auto domain registration"
        ],
        cwd=ROOT,
        check=False
    )

    subprocess.run(
        ["git", "push"],
        cwd=ROOT,
        check=True
    )


def sync_argocd():

    subprocess.run(
        [
            "kubectl",
            "rollout",
            "restart",
            "deployment",
            "argocd-repo-server",
            "-n",
            "argocd"
        ],
        check=False
    )


def create(name, template):

    add_app(name, template)

    generate()

    git_push()

    sync_argocd()


if __name__ == "__main__":

    create(
        "demo",
        "openai"
    )
