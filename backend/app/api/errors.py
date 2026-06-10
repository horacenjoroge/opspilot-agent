from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.request_context import get_request_id
from app.schemas.common import ErrorResponse


logger = logging.getLogger("opspilot.api")


def _error_response(
    *,
    status_code: int,
    detail: str,
    error_code: str,
    request_id: str,
    errors: list[dict] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        detail=detail,
        error_code=error_code,
        request_id=request_id,
        errors=errors or [],
    )
    response = JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
    response.headers["X-Request-ID"] = payload.request_id
    return response


def _resolve_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or get_request_id()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = _resolve_request_id(request)
    logger.warning(
        "http_exception request_id=%s status=%s detail=%s",
        request_id,
        exc.status_code,
        exc.detail,
    )
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _error_response(
        status_code=exc.status_code,
        detail=detail,
        error_code=f"http_{exc.status_code}",
        request_id=request_id,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = _resolve_request_id(request)
    logger.warning(
        "validation_error request_id=%s errors=%s",
        request_id,
        len(exc.errors()),
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Request validation failed.",
        error_code="validation_error",
        request_id=request_id,
        errors=[{"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]} for error in exc.errors()],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _resolve_request_id(request)
    logger.exception(
        "unhandled_exception request_id=%s error_type=%s",
        request_id,
        exc.__class__.__name__,
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error.",
        error_code="internal_server_error",
        request_id=request_id,
    )
