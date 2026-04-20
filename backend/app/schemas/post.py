from datetime import datetime
from typing import Optional
from pydantic import BaseModel, computed_field


class PostCreate(BaseModel):
    platform: str = "both"
    content: str
    scheduled_at: Optional[datetime] = None
    media_asset_id: Optional[int] = None
    brand_persona_id: Optional[int] = None
    generation_prompt: str = ""
    thread_group_id: Optional[str] = None
    thread_sequence_order: int = 0
    is_thread_parent: bool = False


class PostUpdate(BaseModel):
    content: Optional[str] = None
    platform: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    media_asset_id: Optional[int] = None


class PostSchedule(BaseModel):
    scheduled_at: datetime


class MediaAssetOut(BaseModel):
    id: int
    filename: str
    mime_type: Optional[str] = None

    @computed_field
    @property
    def url(self) -> str:
        return f"/uploads/{self.filename}"

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    platform: str
    content: str
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    facebook_post_id: str
    threads_post_id: str
    media_asset_id: Optional[int]
    media_asset: Optional[MediaAssetOut] = None
    brand_persona_id: Optional[int]
    generation_prompt: str
    error_message: str
    is_thread_parent: bool
    thread_group_id: Optional[str]
    thread_sequence_order: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
