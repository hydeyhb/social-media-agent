import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import create_tables
from app.routers import auth, brand, posts, generation, analytics, assets, webhooks
from app.services.scheduler_service import get_scheduler
from app.tasks.analytics_sync_task import run_analytics_sync_sync

settings = get_settings()

app = FastAPI(
    title="Social Media AI Agent",
    description="FB + Threads 全自動社群媒體 AI 管理系統",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(brand.router, prefix="/api/brand", tags=["Brand"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
app.include_router(generation.router, prefix="/api/generate", tags=["Generation"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# Serve uploaded images statically
uploads_path = Path(settings.uploads_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Serve frontend static files in production
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="frontend-assets")


@app.on_event("startup")
async def startup():
    create_tables()
    scheduler = get_scheduler()
    scheduler.start()

    # Register recurring analytics sync every 6 hours
    from apscheduler.triggers.interval import IntervalTrigger
    if not scheduler.get_job("analytics_sync"):
        scheduler.add_job(
            run_analytics_sync_sync,
            trigger=IntervalTrigger(hours=6),
            id="analytics_sync",
            replace_existing=True,
        )
    port = os.environ.get("PORT", "8000")
    print("🚀 Social Media AI Agent started")
    print(f"📖 API Docs: /docs")


@app.on_event("shutdown")
async def shutdown():
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Catch-all: serve frontend index.html for SPA routing
@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    """Serve the frontend SPA. API routes are handled by routers above."""
    if STATIC_DIR.is_dir():
        # Try to serve the exact file first
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for SPA routing
        index_path = STATIC_DIR / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path))
    return {"message": "Social Media AI Agent API", "docs": "/docs"}
