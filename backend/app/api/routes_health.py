from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.core.config import Settings, get_settings
from app.schemas.common import HealthResponse, ReadinessCheck, ReadyResponse


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Return a lightweight liveness response showing the running service name and active LLM provider.",
)
async def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        llm_provider=settings.llm_provider,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description=(
        "Return a deeper readiness response that checks database connectivity and provider configuration. "
        "If the service is not ready, the endpoint returns HTTP 503 with per-check details."
    ),
)
async def readiness_check(
    response: Response,
    db: Session = Depends(get_db_session),
) -> ReadyResponse:
    settings = get_settings()
    checks = {
        "database": _database_check(db),
        "provider": _provider_check(settings),
    }
    ready = all(check.ok for check in checks.values())
    ready_response = ReadyResponse(
        status="ready" if ready else "not_ready",
        service=settings.app_name,
        llm_provider=settings.llm_provider,
        timestamp=datetime.now(timezone.utc),
        checks=checks,
    )
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ready_response


def _database_check(db: Session) -> ReadinessCheck:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return ReadinessCheck(ok=False, detail=f"Database check failed: {exc.__class__.__name__}.")
    return ReadinessCheck(ok=True, detail="Database connection succeeded.")


def _provider_check(settings: Settings) -> ReadinessCheck:
    if settings.llm_provider == "mock":
        return ReadinessCheck(ok=True, detail="Mock provider is configured for local/demo readiness.")
    if settings.llm_provider == "qwen":
        missing = []
        if not settings.qwen_api_key:
            missing.append("QWEN_API_KEY")
        if not settings.qwen_base_url:
            missing.append("QWEN_BASE_URL")
        if missing:
            missing_list = ", ".join(missing)
            return ReadinessCheck(ok=False, detail=f"Missing required Qwen configuration: {missing_list}.")
        return ReadinessCheck(ok=True, detail="Qwen provider configuration is present.")
    return ReadinessCheck(ok=False, detail=f"Unsupported LLM provider '{settings.llm_provider}'.")
