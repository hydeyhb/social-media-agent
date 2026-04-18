import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import create_tables
from app.routers import admin, auth, brand, posts, generation, analytics, assets, webhooks
from app.services.auth_service import decode_access_token
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

# Auth middleware – protect /api/* routes (whitelist exceptions)
AUTH_WHITELIST = {
    ("POST", "/api/admin/login"),
    ("GET", "/api/health"),
    ("GET", "/api/auth/facebook/callback"),
    ("GET", "/api/auth/threads/callback"),
}


@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method

    # Skip non-API paths (frontend, uploads, static)
    if not path.startswith("/api/"):
        return await call_next(request)

    # Skip CORS preflight
    if method == "OPTIONS":
        return await call_next(request)

    # Skip whitelisted exact paths
    if (method, path) in AUTH_WHITELIST:
        return await call_next(request)

    # Skip webhook paths
    if path.startswith("/api/webhooks"):
        return await call_next(request)

    # Verify JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    token = auth_header[7:]
    username = decode_access_token(token)
    if username is None:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    return await call_next(request)


# Routers
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
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


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return """<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="UTF-8"><title>隱私權政策 - Social Media AI Agent</title>
<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#333}h1{color:#1a73e8}</style></head>
<body><h1>隱私權政策</h1>
<p>最後更新日期：2026 年 3 月</p>
<p>Social Media AI Agent（以下簡稱「本應用程式」）尊重您的隱私。本政策說明我們如何收集、使用和保護您的資訊。</p>
<h2>資料收集</h2><p>本應用程式透過 Facebook 和 Threads API 存取您授權的社群媒體帳號資料，包括：貼文內容、互動數據（按讚、留言、分享數）及基本帳號資訊。</p>
<h2>資料用途</h2><p>我們僅將您的資料用於：提供社群媒體管理功能、產生 AI 內容建議、分析貼文成效。</p>
<h2>資料保護</h2><p>您的存取權杖以加密方式儲存，我們不會將您的資料分享給任何第三方。</p>
<h2>資料刪除</h2><p>您可隨時取消授權並要求刪除所有資料，請透過應用程式設定或聯繫我們。</p>
<h2>聯絡方式</h2><p>如有任何隱私相關問題，請聯繫：hydeyhb@gmail.com</p>
</body></html>"""


@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    return """<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="UTF-8"><title>服務條款 - Social Media AI Agent</title>
<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#333}h1{color:#1a73e8}</style></head>
<body><h1>服務條款</h1>
<p>最後更新日期：2026 年 3 月</p>
<p>歡迎使用 Social Media AI Agent。使用本服務即表示您同意以下條款。</p>
<h2>服務說明</h2><p>本應用程式提供社群媒體管理工具，包括 AI 內容生成、排程發布和數據分析。</p>
<h2>使用者責任</h2><p>您應確保透過本服務發布的內容符合 Facebook 和 Threads 的社群守則。</p>
<h2>免責聲明</h2><p>本服務以「現況」提供，不對任何因使用本服務造成的損失負責。</p>
<h2>聯絡方式</h2><p>hydeyhb@gmail.com</p>
</body></html>"""


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
