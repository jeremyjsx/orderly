from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/db")
async def health_check_db(session: SessionDep):
    if settings.ENV != "development":
        return {"status": "disabled"}

    result = await session.execute(text("SELECT 1"))
    ok = result.scalar_one_or_none() is not None
    return {"status": "ok" if ok else "error"}
