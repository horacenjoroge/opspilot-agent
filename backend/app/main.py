from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_approvals import router as approvals_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_demo import router as demo_router
from app.api.routes_health import router as health_router
from app.api.routes_incidents import router as incidents_router
from app.core.config import get_settings
from app.db.session import init_db
from app.ui import STATIC_DIR


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(dashboard_router)
app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(approvals_router)
app.include_router(demo_router)
