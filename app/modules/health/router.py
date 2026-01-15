from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    return {"status": "ok"}


@router.get("/db")
async def health_check_db(session: AsyncSession = Depends(get_db)):
    if settings.ENV != "development":
        return {"status": "disabled"}

    result = await session.execute(text("SELECT 1"))
    ok = result.scalar_one_or_none() is not None
    return {"status": "ok" if ok else "error"}
