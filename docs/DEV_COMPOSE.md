# Dev Compose

This override switches the `api` service to **Dockerfile.dev** with live reload and mounts the working directory.

## Usage
```bash
# Dev stack (override auto-applies)
docker compose up --build
# or explicit:
make up-dev

# Tear down
make down-dev
```

Dashboards are auto-imported from `grafana/dashboards` via provisioning.
