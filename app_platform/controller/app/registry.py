import yaml

REGISTRY_PATH = "/home/shopno/k8s-platform/ai-platform/registry/domains.yaml"


def load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)
