from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.config import settings
from app.events.client import connect, disconnect
from app.modules.health.router import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
    )
    register_routes(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect()
    except Exception:
        pass

    yield

    await disconnect()


def register_routes(app: FastAPI):
    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(health_router)


app = create_app()
