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
- `REQUIRE_APPROVAL_FOR_MEDIUM_RISK`
- `QWEN_API_KEY`
- `QWEN_MODEL`
- `QWEN_BASE_URL`

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

## Health Check Verification

```bash
curl http://127.0.0.1/health
```

Expected response:

```json
{"status":"ok","service":"opspilot","llm_provider":"mock"}
```

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
