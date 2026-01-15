from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(
        title = "Orderly",
        description = "Scalable e-commerce backend with async processing and real-time tracking",
        version = "1.0.0",
        port = 8000,
    )

    return app

app = create_app()

@app.get("/health", tags=["health"])
def health_check():
    return { "status": "ok" }