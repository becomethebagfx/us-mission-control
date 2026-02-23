"""
Mission Control Dashboard — FastAPI Application
Unified API for all US Construction Marketing automation systems.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize data directories and mock data on startup."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "builder" / "sessions").mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "builder" / "uploads").mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "briefs").mkdir(parents=True, exist_ok=True)

    if config.DEMO_MODE:
        from mock_data import seed_all_mock_data
        seed_all_mock_data()

    # Check if Monday Morning Brief should be generated
    try:
        from modules.brief_generator import check_and_generate
        await check_and_generate()
    except Exception:
        pass  # Non-critical, don't block startup

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


# ── Auth Middleware ────────────────────────────────────────────────
from routers.auth import verify_session

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Require authentication for all routes except auth, health, and static."""
    path = request.url.path
    # Skip auth for: auth routes, health check, static assets, login page
    if (
        path.startswith("/auth")
        or path == "/api/health"
        or path.startswith("/static")
    ):
        return await call_next(request)

    # In demo mode, skip auth entirely
    if config.DEMO_MODE:
        return await call_next(request)

    # Check session cookie
    session = verify_session(request)
    if not session:
        if path.startswith("/api/"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/auth/login")

    request.state.user = session
    return await call_next(request)


# ── Routers ───────────────────────────────────────────────────────
from routers import auth
from routers import dashboard, calendar, posts, content, reactivation, settings
from routers import gbp, aeo, reviews, brand_audit, assets, quality
from routers import builder, monitoring, brief

app.include_router(auth.router)
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
app.include_router(quality.router, prefix="/api/quality", tags=["Quality Loop"])
app.include_router(builder.router)
app.include_router(monitoring.router)
app.include_router(brief.router)


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

uploads_dir = Path(__file__).parent / "data" / "builder" / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
async def serve_index(request: Request):
    # In non-demo mode, check auth before serving index
    if not config.DEMO_MODE:
        session = verify_session(request)
        if not session:
            login_path = static_dir / "login.html"
            if login_path.exists():
                return FileResponse(str(login_path))
            return RedirectResponse("/auth/login")

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
