import hmac
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import facebook_service
from app.services.token_service import get_active_token, get_decrypted_access_token

router = APIRouter()
settings = get_settings()


@router.get("/facebook")
async def facebook_webhook_verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.facebook_webhook_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/facebook")
async def facebook_webhook_receive(request: Request, db: Session = Depends(get_db)):
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.facebook_app_secret and signature:
        expected = "sha256=" + hmac.new(
            settings.facebook_app_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)
    page_token = get_decrypted_access_token(db, "facebook")
    if not page_token:
        return {"status": "no_token"}

    # Process comment events
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "feed":
                value = change.get("value", {})
                if value.get("item") == "comment" and value.get("verb") == "add":
                    comment_id = value.get("comment_id", "")
                    post_id = value.get("post_id", "")
                    sender_name = value.get("from", {}).get("name", "")
                    message = value.get("message", "")

                    # Auto-reply with a friendly acknowledgment
                    if comment_id and page_token:
                        try:
                            reply = f"感謝 {sender_name} 的留言！我們已收到您的訊息，會盡快回覆您 🙏"
                            await facebook_service.reply_to_comment(comment_id, reply, page_token)
                        except Exception as e:
                            print(f"Auto-reply failed for comment {comment_id}: {e}")

    return {"status": "ok"}
