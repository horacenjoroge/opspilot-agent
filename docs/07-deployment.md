# Deployment

## Target Environment

The hackathon deployment target is Alibaba Cloud ECS. Local development uses Docker Compose first so the same backend shape can later be promoted to a hosted environment.

## Local Stack

- FastAPI backend
- Environment-driven configuration
- `docker-compose.yml` for local startup
- `/health` endpoint for readiness checks

## Production Direction

The production deployment artifacts now exist:

- `deployment/docker-compose.prod.yml`
- `deployment/Caddyfile` (reverse proxy with automatic HTTPS via Let's Encrypt)
- `deployment/alibaba-cloud.md`

The app is deployed on Alibaba Cloud ECS at `https://47.77.178.251.sslip.io/`.

## Required Environment Variables

- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `LLM_PROVIDER`
- `QWEN_API_KEY`
- `QWEN_MODEL`
- `QWEN_BASE_URL`

## Proof Plan

The final repository should include:

- Alibaba Cloud ECS deployment notes
- reachable `/health` URL
- screenshots or recording references
- a direct path to the Qwen integration code
- a direct path to the architecture diagram

## Verification

For local validation, the backend should be startable with Docker Compose and the health endpoint should return a 200 response.

For production-shape validation, the repository now includes a reverse-proxied Docker Compose stack that can be checked with:

```bash
docker compose -f deployment/docker-compose.prod.yml config
```
