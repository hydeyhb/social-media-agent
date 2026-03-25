from sqlalchemy import Column, DateTime, Integer, String, Text, func
from app.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), default="")
    file_path = Column(Text, nullable=False)
    mime_type = Column(String(100), default="image/jpeg")
    file_size_bytes = Column(Integer, default=0)
    vision_analysis = Column(Text, default="")
    generated_caption = Column(Text, default="")
    facebook_media_id = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now())
