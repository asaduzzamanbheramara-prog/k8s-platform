import yaml
from pathlib import Path

ROOT = Path.home() / "k8s-platform"

REGISTRY = ROOT / "config/domain-registry.yaml"
OUTPUT = ROOT / "gitops/generated"


def load_registry():
    with open(REGISTRY, "r") as f:
        return yaml.safe_load(f)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(content)


def generate_namespace(app_dir, namespace):

    write(
        app_dir / "namespace.yaml",
f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
"""
    )


def generate_deployment(
    app_dir,
    app,
    namespace,
    image,
    port
):

    write(
        app_dir / "deployment.yaml",
f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app}
  namespace: {namespace}

spec:
  replicas: 1

  selector:
    matchLabels:
      app: {app}

  template:
    metadata:
      labels:
        app: {app}

    spec:
      containers:
      - name: {app}
        image: {image}
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: {port}

        resources:
          requests:
            cpu: 100m
            memory: 128Mi

          limits:
            cpu: 500m
            memory: 512Mi

        readinessProbe:
          tcpSocket:
            port: {port}

          initialDelaySeconds: 10
          periodSeconds: 10

        livenessProbe:
          tcpSocket:
            port: {port}

          initialDelaySeconds: 30
          periodSeconds: 20
"""
    )


def generate_service(
    app_dir,
    app,
    port
):

    write(
        app_dir / "service.yaml",
f"""apiVersion: v1
kind: Service
metadata:
  name: {app}
  namespace: {app}

spec:
  selector:
    app: {app}

  ports:
  - name: http
    port: {port}
    targetPort: {port}

  type: ClusterIP
"""
    )


def generate_ingress(
    app_dir,
    app,
    namespace,
    host,
    port
):

    write(
        app_dir / "ingress.yaml",
f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app}
  namespace: {namespace}

spec:
  ingressClassName: traefik

  rules:
  - host: {host}
    http:
      paths:
      - path: /
        pathType: Prefix

        backend:
          service:
            name: {app}
            port:
              number: {port}
"""
    )


def generate_kustomization(app_dir):

    write(
        app_dir / "kustomization.yaml",
"""resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - ingress.yaml
"""
    )


def generate_root_kustomization(apps):

    content = "resources:\n"

    for app in apps:
        content += f"  - {app}\n"

    write(
        OUTPUT / "kustomization.yaml",
        content
    )


def main():

    cfg = load_registry()

    OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    apps = []

    for app, spec in cfg["domains"].items():

        apps.append(app)

        namespace = spec["namespace"]
        host = spec["host"]
        port = spec["port"]
        image = spec["image"]

        app_dir = OUTPUT / app

        generate_namespace(
            app_dir,
            namespace
        )

        generate_deployment(
            app_dir,
            app,
            namespace,
            image,
            port
        )

        generate_service(
            app_dir,
            app,
            port
        )

        generate_ingress(
            app_dir,
            app,
            namespace,
            host,
            port
        )

        generate_kustomization(
            app_dir
        )

        print(f"Generated {app}")

    generate_root_kustomization(apps)

    print()
    print("Done")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
