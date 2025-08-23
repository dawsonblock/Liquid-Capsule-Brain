# TLS Reverse Proxy (Nginx)

## Purpose
Terminates TLS and forwards to the API (port 8000) with security headers.

## One-time (host machine)
- Install **certbot** and obtain a cert:
  ```bash
  sudo certbot certonly --standalone -d cb.example.com
  # certs stored under: /etc/letsencrypt/live/cb.example.com/
  ```

## Run with Compose
```bash
cp .env.reverse-proxy.example .env
# edit CB_DOMAIN, ensure certs exist in /etc/letsencrypt/live/$CB_DOMAIN
docker compose -f docker-compose.yml -f docker-compose.reverse-proxy.yml --env-file .env up --build
```

Proxy listens on **:443** and forwards to `api:8000` inside the Compose network.
