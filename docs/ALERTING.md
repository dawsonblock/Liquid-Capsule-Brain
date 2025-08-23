# Alerting Setup

Grafana starts with **two contact points** provisioned:
- `default-webhook` → uses **GRAFANA_WEBHOOK_URL**
- `default-email`  → uses **GRAFANA_ALERT_EMAILS** via SMTP

## Steps
1. Edit `.env`:
   - Set `GRAFANA_WEBHOOK_URL` (Slack/Discord/Alertmanager/etc).
   - Set `GRAFANA_ALERT_EMAILS` (comma-separated).
   - Configure SMTP: `GRAFANA_SMTP_HOST`, `GRAFANA_SMTP_USER`, `GRAFANA_SMTP_PASSWORD`, `GRAFANA_SMTP_FROM`.
2. Launch stack:
   ```bash
   docker compose up --build
   ```
3. In Grafana → **Alerting → Contact points**, confirm `default-webhook` and `default-email`.
4. Alerts are provisioned in `prometheus/alerts.yml`. Adjust thresholds as needed.


## Advanced Routing Matrix
- **Critical alerts** → Slack channel `#critical-alerts` via `GRAFANA_SLACK_CRITICAL_URL`.
- **Warnings** → Slack channel `#warnings` via `GRAFANA_SLACK_WARNING_URL`.
- **Warnings** also → Email (`GRAFANA_ALERT_EMAILS`).


## Slack Routing Matrix
- `severity=critical` → **slack-critical** (no mute timing)
- `severity=warning`  → **slack-warning** (muted nights/weekends) + **email**

To change, edit `grafana/provisioning/alerting/contacts_and_policy.yml`.


## Critical Paging Windows
- `severity=critical` → **slack-critical**
  - Active paging: 08:00–22:00 weekdays
  - Muted: nights + weekends (still logged in default-webhook)
- `severity=warning` → **slack-warning** + **email**
  - Muted: nights + weekends


## Critical Paging Windows
- **On-hours (Mon–Fri 08:00–22:00):** route to `slack-critical`
- **Off-hours (nights + weekends):** route to `pager-critical` (webhook)

To change hours, edit `grafana/provisioning/alerting/contacts_and_policy.yml` in `muteTimings`.
