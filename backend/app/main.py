"""FastAPI application entry point and SPA serving."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.api.routes import router
from app.store import CareerStore


def resolve_root(explicit: Path | None = None) -> Path:
    """Find the project root by locating data/, so the same code works whether the
    app lives at repo/backend/app (local) or /app/app (container)."""

    if explicit is not None:
        return explicit
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "employees.json").exists():
            return parent
    return here.parents[2]


def create_app(data_root: Path | None = None) -> FastAPI:
    root = resolve_root(data_root)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        store = CareerStore(data_root=root)
        store.load()
        app.state.store = store
        yield

    app = FastAPI(title="Career Quest API", version="1.0", lifespan=lifespan)
    app.include_router(router)
    dist_dir = root / "frontend" / "dist"

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        index = dist_dir / "index.html"
        candidate = dist_dir / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Frontend build not found")

    return app


app = create_app()
