import urllib.parse
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import facebook_service, threads_service
from app.services.token_service import get_active_token, save_token, days_until_expiry
from app.services.scheduler_service import schedule_token_refresh
from app.schemas.token import TokenStatusOut

router = APIRouter()
settings = get_settings()


# ─── Facebook ────────────────────────────────────────────────────────────────

@router.get("/facebook/login")
async def facebook_login():
    params = urllib.parse.urlencode({
        "client_id": settings.facebook_app_id,
        "redirect_uri": settings.facebook_redirect_uri,
        "scope": "pages_manage_posts,pages_read_engagement,pages_show_list,pages_read_user_content",
        "response_type": "code",
    })
    return RedirectResponse(f"https://www.facebook.com/v19.0/dialog/oauth?{params}")


@router.get("/facebook/callback")
async def facebook_callback(code: str, db: Session = Depends(get_db)):
    # 1. Exchange code for short-lived token
    short_data = await facebook_service.exchange_code_for_token(
        code,
        settings.facebook_app_id,
        settings.facebook_app_secret,
        settings.facebook_redirect_uri,
    )
    short_token = short_data.get("access_token", "")

    # 2. Upgrade to long-lived user token (60 days)
    long_data = await facebook_service.exchange_for_long_lived_token(
        short_token, settings.facebook_app_id, settings.facebook_app_secret
    )
    long_token = long_data.get("access_token", "")

    # 3. Get page tokens — use the first page's never-expiring page token
    pages = await facebook_service.get_pages(long_token)
    if not pages:
        raise HTTPException(status_code=400, detail="No Facebook Pages found. Please create a Page first.")

    page = pages[0]
    save_token(
        db,
        platform="facebook",
        token_type="page",
        access_token=page["access_token"],
        expires_at=None,  # Page tokens don't expire
        page_id=page["id"],
        page_name=page["name"],
        scope=["pages_manage_posts", "pages_read_engagement"],
    )
    return RedirectResponse(f"{settings.frontend_url}/?connected=facebook")


# ─── Threads ─────────────────────────────────────────────────────────────────

@router.get("/threads/login")
async def threads_login():
    params = urllib.parse.urlencode({
        "client_id": settings.threads_app_id,
        "redirect_uri": settings.threads_redirect_uri,
        "scope": "threads_basic,threads_content_publish",
        "response_type": "code",
    })
    return RedirectResponse(f"https://www.threads.net/oauth/authorize?{params}")


@router.get("/threads/callback")
async def threads_callback(code: str, db: Session = Depends(get_db)):
    # 1. Exchange code for short-lived token
    try:
        short_data = await threads_service.exchange_code_for_token(
            code,
            settings.threads_app_id,
            settings.threads_app_secret,
            settings.threads_redirect_uri,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Threads token exchange failed: {e}")
    short_token = short_data.get("access_token", "")
    user_id = short_data.get("user_id", "")

    # 2. Exchange for long-lived token (60 days)
    long_data = await threads_service.exchange_for_long_lived_token(
        short_token, settings.threads_app_secret
    )
    long_token = long_data.get("access_token", "")
    expires_in = long_data.get("expires_in", 5184000)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    token_record = save_token(
        db,
        platform="threads",
        token_type="user_long",
        access_token=long_token,
        expires_at=expires_at,
        user_id=str(user_id),
        scope=["threads_basic", "threads_content_publish"],  # Add more scopes as they are enabled in Meta Developer
    )

    # Schedule auto-refresh at day 50
    refresh_at = expires_at - timedelta(days=10)
    schedule_token_refresh(token_record.id, refresh_at, "threads")

    return RedirectResponse(f"{settings.frontend_url}/?connected=threads")


# ─── Status ──────────────────────────────────────────────────────────────────

@router.get("/status")
async def auth_status(db: Session = Depends(get_db)):
    statuses = []
    for platform in ["facebook", "threads"]:
        token = get_active_token(db, platform)
        if token:
            statuses.append(TokenStatusOut(
                platform=platform,
                is_connected=True,
                token_type=token.token_type,
                page_name=token.page_name or token.user_id,
                page_id=token.page_id or token.user_id,
                expires_at=token.expires_at,
                days_until_expiry=days_until_expiry(token),
            ))
        else:
            statuses.append(TokenStatusOut(
                platform=platform,
                is_connected=False,
                token_type="",
                page_name="",
                page_id="",
                expires_at=None,
                days_until_expiry=None,
            ))
    return statuses


@router.delete("/revoke/{platform}")
async def revoke_token(platform: str, db: Session = Depends(get_db)):
    from app.models.token import OAuthToken
    db.query(OAuthToken).filter(
        OAuthToken.platform == platform,
        OAuthToken.is_active == True,
    ).update({"is_active": False})
    db.commit()
    return {"message": f"{platform} token revoked"}
