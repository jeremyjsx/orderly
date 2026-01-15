from fastapi import FastAPI
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title = settings.APP_NAME,
        description = settings.DESCRIPTION,
        version = settings.VERSION,
        port = settings.PORT,
    )

    return app

app = create_app()

@app.get("/health", tags=["health"])
def health_check():
    return { "status": "ok" }