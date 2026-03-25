import asyncio
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal
from app.models.token import OAuthToken
from app.services import threads_service
from app.services.token_service import decrypt_token, encrypt_token
from app.services.scheduler_service import schedule_token_refresh


async def _refresh_threads(token_record: OAuthToken, db) -> None:
    raw_token = decrypt_token(token_record.access_token)
    data = await threads_service.refresh_long_lived_token(raw_token)
    new_token = data.get("access_token", raw_token)
    expires_in = data.get("expires_in", 5184000)  # default 60 days
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    token_record.access_token = encrypt_token(new_token)
    token_record.expires_at = expires_at
    token_record.refreshed_at = datetime.now(timezone.utc)
    db.commit()

    # Schedule next refresh at day 50
    next_refresh = expires_at - timedelta(days=10)
    schedule_token_refresh(token_record.id, next_refresh, "threads")
    print(f"[Token Refresh] Threads token refreshed. Next refresh: {next_refresh}")


async def refresh_token_task(token_id: int, platform: str) -> None:
    db = SessionLocal()
    try:
        token_record = db.query(OAuthToken).filter(OAuthToken.id == token_id).first()
        if not token_record or not token_record.is_active:
            return

        if platform == "threads":
            await _refresh_threads(token_record, db)
        # Facebook page tokens don't expire when permissions are granted correctly
    finally:
        db.close()


def refresh_token_task_sync(token_id: int, platform: str) -> None:
    asyncio.run(refresh_token_task(token_id, platform))
