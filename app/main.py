from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
    )

    return app


app = create_app()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
async def health_check_db(session: AsyncSession = Depends(get_db)):
    if settings.ENV != "development":
        return {"status": "disabled"}

    result = await session.execute(text("SELECT 1"))
    ok = result.scalar_one_or_none() is not None
    return {"status": "ok" if ok else "error"}
