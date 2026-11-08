import logging

from fastapi import FastAPI

from .auth.router import router as auth_router
from .todos.router import router as todo_router
from .core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="EY Todo API",
        version="0.1.0",
        summary="Todo API backend with authentication",  
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

app.include_router(auth_router, prefix="/api")
app.include_router(todo_router, prefix="/api")