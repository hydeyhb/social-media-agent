from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from app.database import Base


class BrandPersona(Base):
    __tablename__ = "brand_personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tone = Column(String(100), default="professional")
    style_notes = Column(Text, default="")
    target_audience = Column(Text, default="")
    keywords = Column(Text, default="[]")        # JSON array string
    avoid_phrases = Column(Text, default="[]")   # JSON array string
    emoji_usage = Column(String(20), default="moderate")  # none / moderate / heavy
    post_length_preference = Column(String(20), default="medium")  # short / medium / long
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
