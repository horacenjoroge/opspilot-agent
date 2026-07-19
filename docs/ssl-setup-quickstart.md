# SSL Setup Quickstart

Current status: Implemented

HTTPS is terminated by Caddy, which obtains and renews a free Let's Encrypt
certificate automatically. The public domain uses sslip.io wildcard DNS, so no
purchased domain is required: `<ECS-public-IP>.sslip.io` resolves to the
instance.

## Current Deployment Pieces

- Caddy config: `deployment/Caddyfile`
- production compose: `deployment/docker-compose.prod.yml` (`caddy` service, ports 80 + 443)
- domain: set via `SITE_DOMAIN` env var (defaults to `47.77.178.251.sslip.io`)

## How It Works

1. Caddy listens on 80 and 443.
2. On first start it requests a Let's Encrypt certificate for `SITE_DOMAIN`
   via the HTTP-01 challenge on port 80.
3. Certificates persist in the `caddy_data` volume and renew automatically.
4. HTTP requests for the domain redirect to HTTPS; raw-IP HTTP access keeps
   working for health checks.

## Requirements

- TCP 80 and 443 open in the ECS security group
- `SITE_DOMAIN` resolving to the instance public IP (automatic with sslip.io)

## Verification

- `curl https://47.77.178.251.sslip.io/health`
- confirm certificate validity in the browser
- confirm the dashboard loads over HTTPS
