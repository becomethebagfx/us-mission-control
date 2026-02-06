"""
Mission Control Dashboard — FastAPI Application
Unified API for all US Construction Marketing automation systems.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize mock data on startup if in demo mode."""
    if config.DEMO_MODE:
        from mock_data import seed_all_mock_data
        seed_all_mock_data()
    yield


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
from routers import dashboard, calendar, posts, content, reactivation, settings
from routers import gbp, aeo, reviews, brand_audit, assets

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(reactivation.router, prefix="/api/reactivation", tags=["Reactivation"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(gbp.router, prefix="/api/gbp", tags=["GBP"])
app.include_router(aeo.router, prefix="/api/aeo", tags=["AEO"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(brand_audit.router, prefix="/api/brand-audit", tags=["Brand Audit"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])


# ── Health Check ──────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "demo_mode": config.DEMO_MODE,
        "companies": len(config.ACTIVE_COMPANIES),
    }


# ── Static Files + SPA Fallback ──────────────────────────────────
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_index():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        {"message": "Mission Control API", "docs": "/docs"},
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)
