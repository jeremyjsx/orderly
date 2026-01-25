from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.core.redis import connect_redis, disconnect_redis
from app.events.client import connect, disconnect
from app.modules.health.router import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    register_middlewares(app)
    register_routes(app)

    return app


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect()
    except Exception:
        pass

    try:
        await connect_redis()
    except Exception:
        pass

    yield

    await disconnect()
    await disconnect_redis()


def register_routes(app: FastAPI):
    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(health_router)


app = create_app()
