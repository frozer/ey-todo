from fastapi import FastAPI

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
