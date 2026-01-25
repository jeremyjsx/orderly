from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import SessionDep, require_admin
from app.core.redis import is_redis_connected
from app.events.client import is_connected as is_rabbitmq_connected
from app.modules.users.models import User

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@router.get("/db")
async def health_check_db(
    session: SessionDep, admin_user: User = Depends(require_admin)
):
    """Database health check (admin only)."""
    result = await session.execute(text("SELECT 1"))
    ok = result.scalar_one_or_none() is not None
    return {"status": "ok" if ok else "error"}


@router.get("/redis")
async def health_check_redis(admin_user: User = Depends(require_admin)):
    """Redis health check (admin only)."""
    ok = await is_redis_connected()
    return {"status": "ok" if ok else "error"}


@router.get("/rabbitmq")
async def health_check_rabbitmq(admin_user: User = Depends(require_admin)):
    """RabbitMQ health check (admin only)."""
    ok = await is_rabbitmq_connected()
    return {"status": "ok" if ok else "error"}


@router.get("/ready")
async def readiness_check(session: SessionDep):
    """Readiness check for all services."""
    db_ok = False
    redis_ok = False
    rabbitmq_ok = False

    try:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar_one_or_none() is not None
    except Exception:
        pass

    redis_ok = await is_redis_connected()
    rabbitmq_ok = await is_rabbitmq_connected()

    all_ok = db_ok and redis_ok and rabbitmq_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "services": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
            "rabbitmq": "ok" if rabbitmq_ok else "error",
        },
    }
