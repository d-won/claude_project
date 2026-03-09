"""FastAPI main application for Financial Analysis Platform."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routers import companies, analysis

app = FastAPI(
    title="Financial Analysis Platform",
    description="Global financial analysis with SWOT and DCF valuation for KR, JP, EU, US markets",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(analysis.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve static frontend in production
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
_index_html = STATIC_DIR / "index.html"

if _index_html.exists():
    # Mount assets directory if it exists
    _assets_dir = STATIC_DIR / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(_index_html))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_index_html))
