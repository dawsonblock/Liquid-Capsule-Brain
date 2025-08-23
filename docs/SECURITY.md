# Security Notes

- Never expose `/docs` and `/metrics` publicly without auth proxy.
- Require `ADMIN_TOKEN` for overseer and configuration endpoints.
- Rate-limit public endpoints (nginx/traefik).
- Validate tool invocations rigorously (command allowlist).
