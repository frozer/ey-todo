import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth.router import router as auth_router
from .auth.session import CSRF_HEADER
from .core.config import Settings, get_settings
from .core.origin import origin_check_middleware
from .todos.router import router as todo_router
from .todos.service import InvalidNeighbours, TodoNotFound
from .webapp.router import mount_webapp

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

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

    # an origin allowed to call cross-origin must also pass the origin check
    trusted = [*settings.trusted_origins, *settings.cors_origins]
    app.middleware("http")(origin_check_middleware(trusted))

    # added last so it runs first: CORS preflights are answered before the origin check
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type", CSRF_HEADER],
        )

    app.include_router(auth_router, prefix="/api")
    app.include_router(todo_router, prefix="/api")

    # catch-all SPA route: must be registered after every other route
    mount_webapp(app, settings.webapp_dir)
    return app


app = create_app()
