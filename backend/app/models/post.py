from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), default="both")  # facebook / threads / both
    content = Column(Text, nullable=False)
    status = Column(String(20), default="draft")   # draft / scheduled / published / failed
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    facebook_post_id = Column(String(255), default="")
    threads_post_id = Column(String(255), default="")
    media_asset_id = Column(Integer, ForeignKey("media_assets.id"), nullable=True)
    brand_persona_id = Column(Integer, ForeignKey("brand_personas.id"), nullable=True)
    generation_prompt = Column(Text, default="")
    error_message = Column(Text, default="")

    # Thread series support
    is_thread_parent = Column(Boolean, default=False)
    thread_group_id = Column(String(36), nullable=True, index=True)  # UUID
    thread_sequence_order = Column(Integer, default=0)

    apscheduler_job_id = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
