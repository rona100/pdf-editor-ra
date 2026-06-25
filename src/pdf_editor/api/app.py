from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="PDF Editor", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api")

    import os
    frontend_dist_env = os.environ.get("FRONTEND_DIST")
    if frontend_dist_env:
        frontend_build = Path(frontend_dist_env)
    else:
        frontend_build = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if frontend_build.exists():
        app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="static")

    return app


app = create_app()
