from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TokenStatusOut(BaseModel):
    platform: str
    is_connected: bool
    token_type: str
    page_name: str
    page_id: str
    expires_at: Optional[datetime]
    days_until_expiry: Optional[int]
