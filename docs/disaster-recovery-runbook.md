# Disaster Recovery Runbook

## If the Backend Is Down

1. check process or container status
2. review application logs
3. restart Uvicorn or Docker services
4. verify `/health`

## If the Qwen API Fails

- switch to `MockProvider` for local demo continuity if appropriate
- verify `QWEN_API_KEY`, `QWEN_MODEL`, and `QWEN_BASE_URL`
- note that the agent has safe fallback behavior for runtime failures

## If the Database Is Unavailable

- verify the SQLite file path and filesystem permissions
- restart the app if the DB file was temporarily inaccessible
- note that there is no external database HA setup in the current implementation

## If Deployment Fails

- check Docker build logs
- verify environment variables
- verify Nginx config if used
- validate `/health` after restart

## Restoring From Backup

Automated backup/restore tooling is not implemented today.

Future Work:
- scheduled database backups
- backup verification
- documented restore drills
