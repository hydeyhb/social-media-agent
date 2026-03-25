import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.token import OAuthToken

settings = get_settings()


def _fernet() -> Fernet:
    key = settings.token_encryption_key
    if not key:
        # Generate a key for first-run if none configured (prints warning)
        print("WARNING: TOKEN_ENCRYPTION_KEY not set. Generating ephemeral key (tokens lost on restart).")
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(raw: str) -> str:
    return _fernet().encrypt(raw.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _fernet().decrypt(encrypted.encode()).decode()


def save_token(
    db: Session,
    platform: str,
    token_type: str,
    access_token: str,
    expires_at: Optional[datetime] = None,
    page_id: str = "",
    page_name: str = "",
    user_id: str = "",
    scope: list = None,
    refresh_token: str = "",
) -> OAuthToken:
    # Deactivate previous tokens for this platform
    db.query(OAuthToken).filter(
        OAuthToken.platform == platform,
        OAuthToken.is_active == True,
    ).update({"is_active": False})

    token = OAuthToken(
        platform=platform,
        token_type=token_type,
        access_token=encrypt_token(access_token),
        refresh_token=encrypt_token(refresh_token) if refresh_token else "",
        expires_at=expires_at,
        page_id=page_id,
        page_name=page_name,
        user_id=user_id,
        scope=json.dumps(scope or []),
        is_active=True,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_active_token(db: Session, platform: str) -> Optional[OAuthToken]:
    return (
        db.query(OAuthToken)
        .filter(OAuthToken.platform == platform, OAuthToken.is_active == True)
        .order_by(OAuthToken.created_at.desc())
        .first()
    )


def get_decrypted_access_token(db: Session, platform: str) -> Optional[str]:
    token = get_active_token(db, platform)
    if not token:
        return None
    return decrypt_token(token.access_token)


def days_until_expiry(token: OAuthToken) -> Optional[int]:
    if not token.expires_at:
        return None
    now = datetime.now(timezone.utc)
    expires = token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    delta = (expires - now).days
    return max(delta, 0)


def is_expired(token: OAuthToken) -> bool:
    d = days_until_expiry(token)
    return d is not None and d <= 0
