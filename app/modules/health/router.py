from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import SessionDep, require_admin
from app.modules.users.models import User

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/db")
async def health_check_db(
    session: SessionDep, admin_user: User = Depends(require_admin)
):
    """Database health check (admin only)."""
    result = await session.execute(text("SELECT 1"))
    ok = result.scalar_one_or_none() is not None
    return {"status": "ok" if ok else "error"}
