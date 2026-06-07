# SSL Setup Quickstart

Current status: Partial / Future Work

Nginx configuration exists in the repo, but a domain-specific HTTPS deployment is not fully implemented in the current project state.

## Current Deployment Pieces

- Nginx config: `deployment/nginx.conf`
- production compose: `deployment/docker-compose.prod.yml`

## Future HTTPS Setup

1. point a domain to the ECS instance
2. configure Nginx server blocks for the domain
3. install Certbot
4. request certificates
5. reload Nginx
6. verify HTTPS and redirect behavior

## Verification

- confirm `https://your-domain/health`
- confirm certificate validity
- confirm Nginx proxying to FastAPI
