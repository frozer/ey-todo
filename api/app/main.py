import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth.router import router as auth_router
from .core.config import get_settings
from .todos.router import router as todo_router
from .todos.service import InvalidNeighbours, TodoNotFound

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="EY Todo API",
        version="0.1.0",
        summary="Todo API backend with authentication"
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(TodoNotFound)
    async def todo_not_found(_request: Request, _exc: TodoNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": [{"msg": "todo_not_found"}]},
        )

    @app.exception_handler(InvalidNeighbours)
    async def stale_order(_request: Request, _exc: InvalidNeighbours) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": [{"msg": "stale_order"}]},
        )

    return app


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust this to your specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(todo_router, prefix="/api")