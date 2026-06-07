# Alibaba Cloud Deployment Proof

## Alibaba Cloud Service Used

Target service:
- Alibaba Cloud ECS

## Backend Deployment Shape

- FastAPI backend
- optional Nginx reverse proxy
- Docker Compose production-shaped deployment artifact

Relevant files:
- [deployment/docker-compose.prod.yml](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/deployment/docker-compose.prod.yml:1)
- [deployment/nginx.conf](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/deployment/nginx.conf:1)

## Public Backend URL

Placeholder:
- `TODO: add public ECS URL`

## Health Endpoint

- `/health`

## How Judges Can Verify the Backend

1. open the public backend URL when available
2. visit `/health`
3. inspect `/docs` for the OpenAPI surface
4. use `/evals` in the dashboard or `/api/evals/run` for deterministic scenario checks

## Qwen Reference

Qwen integration code:
- [backend/app/services/qwen_client.py](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/backend/app/services/qwen_client.py:1)
- [backend/app/llm/qwen_provider.py](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/backend/app/llm/qwen_provider.py:1)

## Notes For Devpost Submission

- attach the public ECS URL when available
- include `/health` proof
- include dashboard screenshots
- include architecture diagram

## Privacy and Safety

Do not include account IDs, secrets, private URLs, or credentials in this document.
