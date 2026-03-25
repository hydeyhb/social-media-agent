from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from app.database import Base


class PostAnalytics(Base):
    __tablename__ = "post_analytics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    synced_at = Column(DateTime, server_default=func.now())


class EngagementSnapshot(Base):
    __tablename__ = "engagement_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    snapshot_at = Column(DateTime, server_default=func.now())
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)


class PostingTimeStat(Base):
    __tablename__ = "posting_time_stats"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)
    day_of_week = Column(Integer, nullable=False)   # 0=Mon … 6=Sun
    hour_of_day = Column(Integer, nullable=False)   # 0–23
    avg_engagement_rate = Column(Float, default=0.0)
    sample_count = Column(Integer, default=0)
    last_computed_at = Column(DateTime, server_default=func.now())
