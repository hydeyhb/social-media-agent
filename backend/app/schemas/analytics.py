from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PostAnalyticsOut(BaseModel):
    id: int
    post_id: int
    platform: str
    impressions: int
    reach: int
    likes: int
    comments: int
    shares: int
    clicks: int
    engagement_rate: float
    synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class PostingTimeStatOut(BaseModel):
    day_of_week: int
    hour_of_day: int
    avg_engagement_rate: float
    sample_count: int

    class Config:
        from_attributes = True
