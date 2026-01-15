from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.config import settings
from app.modules.health.router import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
    )
    register_routes(app)

    return app


def register_routes(app: FastAPI):
    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(health_router)


app = create_app()
