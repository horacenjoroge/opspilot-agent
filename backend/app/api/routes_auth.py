from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_auth_context, resolve_optional_auth_context
from app.api.dependencies import get_db_session
from app.core.config import get_settings
from app.schemas.auth import AuthStatusResponse, LoginRequest, LoginResponse, UserRead
from app.schemas.common import ErrorResponse
from app.services.auth import AuthenticationError, AuthService
from app.ui import TEMPLATES_DIR


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

api_router = APIRouter(prefix="/api/auth", tags=["auth"])
page_router = APIRouter(include_in_schema=False)


def _set_auth_cookie(response: JSONResponse | RedirectResponse, session_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.auth_session_ttl_hours * 3600,
    )


@api_router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and create a session",
    description="Authenticate a user with email and password, then issue a session cookie for API and dashboard access.",
    responses={401: {"model": ErrorResponse, "description": "Credentials were invalid."}},
)
async def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> JSONResponse:
    settings = get_settings()
    if not settings.enable_auth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication is disabled.")
    service = AuthService(db)
    try:
        user = service.authenticate(payload.email, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    session = service.create_session(user)
    body = LoginResponse(
        user=UserRead.model_validate(user),
        session_expires_at=session.expires_at,
    ).model_dump(mode="json")
    response = JSONResponse(content=body)
    _set_auth_cookie(response, session.session_token)
    return response


@api_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke session",
    description="Revoke the current session cookie or bearer token.",
)
async def logout(
    request: Request,
    db: Session = Depends(get_db_session),
    _: object = Depends(get_current_auth_context),
) -> JSONResponse:
    settings = get_settings()
    token = request.cookies.get(settings.auth_session_cookie_name)
    authorization = request.headers.get("Authorization", "")
    if not token and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):].strip()
    if token:
        AuthService(db).revoke_session(token)
    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(settings.auth_session_cookie_name)
    return response


@api_router.get(
    "/me",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current auth status",
    description="Return whether auth is enabled and the current authenticated user if present.",
)
async def auth_status(
    request: Request,
    db: Session = Depends(get_db_session),
) -> AuthStatusResponse:
    settings = get_settings()
    context = resolve_optional_auth_context(request, db)
    return AuthStatusResponse(
        auth_enabled=settings.enable_auth,
        dashboard_auth_enabled=settings.enable_dashboard_auth,
        user=UserRead.model_validate(context.user) if context.user else None,
    )


@page_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    settings = get_settings()
    if not settings.enable_auth:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "auth_enabled": False,
                "dashboard_auth_enabled": settings.enable_dashboard_auth,
            },
        )
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "auth_enabled": True,
            "dashboard_auth_enabled": settings.enable_dashboard_auth,
            "next_path": request.query_params.get("next", "/"),
        },
    )


@page_router.get("/logout")
async def logout_page(request: Request, db: Session = Depends(get_db_session)) -> RedirectResponse:
    settings = get_settings()
    token = request.cookies.get(settings.auth_session_cookie_name)
    if token:
        AuthService(db).revoke_session(token)
    response = RedirectResponse(url=f"/login?next={quote('/')}", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.auth_session_cookie_name)
    return response
