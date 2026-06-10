from contextlib import asynccontextmanager
import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api.errors import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.api.routes_approvals import router as approvals_router
from app.api.routes_auth import api_router as auth_router
from app.api.routes_auth import page_router as auth_page_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_demo import router as demo_router
from app.api.routes_evaluations import router as evaluations_router
from app.api.routes_health import router as health_router
from app.api.routes_incidents import router as incidents_router
from app.core.config import get_settings
from app.core.request_context import reset_request_id, set_request_id
from app.db.session import init_db
from app.ui import STATIC_DIR


logger = logging.getLogger("opspilot.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
        )
        return response

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="OpsPilot API",
        summary="Evidence-first SRE autopilot backend for Qwen Cloud Global AI Hackathon Track 4.",
        description=(
            "OpsPilot is a backend-controlled incident triage and safe remediation system. "
            "It combines Qwen Cloud reasoning, allowlisted tools, approval-gated remediation, "
            "auditability, timeline persistence, and judge-friendly evaluation scenarios."
        ),
        version="0.1.0",
        lifespan=lifespan,
        contact={"name": "OpsPilot Hackathon Project"},
        license_info={"name": "MIT"},
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(auth_router)
    app.include_router(auth_page_router)
    if settings.enable_dashboard:
        app.include_router(dashboard_router)
    app.include_router(health_router)
    app.include_router(incidents_router)
    app.include_router(approvals_router)
    if settings.enable_demo_routes:
        app.include_router(demo_router)
    if settings.enable_eval_routes:
        app.include_router(evaluations_router)
    return app


app = create_app()
