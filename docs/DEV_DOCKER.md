# Dev Docker

## Build & run
```bash
docker build -f Dockerfile.dev -t capsule-brain-dev:latest .
docker run --rm -it --name cb-dev \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd):/app \
  capsule-brain-dev:latest
# API: http://127.0.0.1:8000  (reload on file change)
```
