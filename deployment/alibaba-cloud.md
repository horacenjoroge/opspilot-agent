# Alibaba Cloud Deployment Proof

## Status

This file is the deployment proof template for the final hackathon submission. The production packaging and proof structure now exist in the repository, but the live Alibaba Cloud ECS deployment details still need to be filled in after deployment.

Local production-shape verification completed on June 7, 2026:

- `docker compose -f deployment/docker-compose.prod.yml config` resolved successfully
- `docker compose -f deployment/docker-compose.prod.yml up -d --no-build` started backend and Nginx locally
- `curl http://127.0.0.1/health` returned a healthy response through Nginx

What is still pending is the actual ECS deployment and public proof artifacts.

## Deployment Target

- Provider: Alibaba Cloud ECS
- App: OpsPilot backend + built-in dashboard
- Runtime shape: FastAPI backend behind Nginx using Docker Compose
- Health check path: `/health`

## ECS Instance Details

Fill these in after deployment:

- Region:
- Instance type:
- Public IP or domain:
- Operating system:
- Security group notes:

Do not commit secrets, private keys, or full internal network details.

## Deployment Method

Recommended production steps:

1. Copy the repository to the ECS instance.
2. Create a production `.env` file with:
   - `APP_ENV=production`
   - `APP_HOST=0.0.0.0`
   - `APP_PORT=8000`
   - `APP_RELOAD=false`
   - `LLM_PROVIDER=qwen`
   - `QWEN_API_KEY=...`
   - `QWEN_MODEL=qwen3.7-plus`
   - `QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
3. Start the stack with:

```bash
docker compose -f deployment/docker-compose.prod.yml up --build -d
```

4. Verify:

```bash
curl http://YOUR_HOST/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "opspilot",
  "llm_provider": "qwen"
}
```

## Live Proof

Fill these in after the live deployment is available:

- Live health URL:
- Dashboard URL:
- Screenshot link:
- Demo recording link:

## Repository Links

- Qwen integration: `backend/app/services/qwen_client.py`
- Provider wrapper: `backend/app/llm/qwen_provider.py`
- Architecture doc: `docs/02-architecture.md`
- Deployment doc: `docs/07-deployment.md`
- Production compose: `deployment/docker-compose.prod.yml`
- Nginx config: `deployment/nginx.conf`

## Submission Notes

For the final Devpost submission, this file should show that:

- the backend runs on Alibaba Cloud
- `/health` is reachable publicly
- the Qwen integration path is visible in the repo
- the architecture and deployment story are easy for judges to verify
