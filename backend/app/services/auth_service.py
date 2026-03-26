from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Compare password. If stored value is a bcrypt hash, verify against it;
    otherwise do a plain-text comparison."""
    if stored_password.startswith("$2b$") or stored_password.startswith("$2a$"):
        return pwd_context.verify(plain_password, stored_password)
    return plain_password == stored_password


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode JWT and return the subject (username). Returns None on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
