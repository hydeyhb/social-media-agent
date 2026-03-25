from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class BrandPersonaCreate(BaseModel):
    name: str
    tone: str = "professional"
    style_notes: str = ""
    target_audience: str = ""
    keywords: List[str] = []
    avoid_phrases: List[str] = []
    emoji_usage: str = "moderate"
    post_length_preference: str = "medium"


class BrandPersonaUpdate(BrandPersonaCreate):
    name: Optional[str] = None


class BrandPersonaOut(BaseModel):
    id: int
    name: str
    tone: str
    style_notes: str
    target_audience: str
    keywords: List[str]
    avoid_phrases: List[str]
    emoji_usage: str
    post_length_preference: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
