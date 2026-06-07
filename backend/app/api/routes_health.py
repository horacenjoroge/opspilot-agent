from fastapi import APIRouter, status

from app.core.config import get_settings
from app.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Return a lightweight readiness response showing the running service name and active LLM provider.",
)
async def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        llm_provider=settings.llm_provider,
    )
