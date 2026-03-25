from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from app.database import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)   # facebook / threads
    token_type = Column(String(20), default="page") # user_short / user_long / page
    access_token = Column(Text, nullable=False)      # Fernet-encrypted
    refresh_token = Column(Text, default="")
    expires_at = Column(DateTime, nullable=True)     # NULL = never expires
    page_id = Column(String(100), default="")
    page_name = Column(String(255), default="")
    user_id = Column(String(100), default="")
    scope = Column(Text, default="[]")               # JSON array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    refreshed_at = Column(DateTime, server_default=func.now())
