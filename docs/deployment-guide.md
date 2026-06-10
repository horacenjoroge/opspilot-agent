# Deployment Guide

## Target

Alibaba Cloud ECS

## Deployment Shape

- FastAPI application
- optional Nginx reverse proxy
- Docker Compose production-shaped stack
- SQLite database file in the current implementation

## Required Environment Variables

- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `DATABASE_URL`
- `LLM_PROVIDER`
- `ENABLE_DEMO_ROUTES`
- `ENABLE_EVAL_ROUTES`
- `ENABLE_DASHBOARD`
- `REQUIRE_APPROVAL_FOR_MEDIUM_RISK`
- `QWEN_API_KEY`
- `QWEN_MODEL`
- `QWEN_BASE_URL`

Feature flag guidance:

- keep all three enabled for hackathon demos
- disable `ENABLE_DEMO_ROUTES` and `ENABLE_EVAL_ROUTES` if you want a cleaner non-demo API surface
- disable `ENABLE_DASHBOARD` if you want only the JSON API surface

## Docker / Compose

Local production-shaped config:

```bash
docker compose -f deployment/docker-compose.prod.yml up --build -d
curl http://127.0.0.1/health
docker compose -f deployment/docker-compose.prod.yml down
```

## Manual Deployment Steps

If you do not use Docker:

1. install Python dependencies
2. copy `.env`
3. start Uvicorn behind Nginx
4. verify `/health`
5. verify `/ready`

## Health And Readiness Verification

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/ready
```

Expected `/health` response:

```json
{"status":"ok","service":"opspilot","llm_provider":"mock"}
```

Expected `/ready` behavior:

- `200` with `status=ready` when the DB check and provider check pass
- `503` with `status=not_ready` when a required dependency or Qwen configuration is missing

## Logs

- Uvicorn logs
- Nginx logs if Nginx is used
- audit and timeline records inside the application database

## Restarting Services

- Docker: restart the relevant containers
- manual: restart Uvicorn and Nginx

## Updating Deployment

- pull latest code
- rebuild image if using Docker
- restart the stack
- verify `/health`

## Rollback Notes

Rollback is manual today. There is no automated migration rollback or blue-green deployment flow.

## Common Deployment Errors

- Qwen 401: wrong key or wrong base URL
- port conflicts on `8000`
- Docker daemon not running locally
- missing `.env` values
