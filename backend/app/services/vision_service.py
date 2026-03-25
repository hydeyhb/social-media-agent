import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.asset import MediaAsset
from app.models.brand import BrandPersona
from app.services import openai_service

settings = get_settings()


async def process_upload(
    file: UploadFile,
    persona: BrandPersona,
    db: Session,
    platform: str = "both",
) -> MediaAsset:
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix or ".jpg"
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = uploads_dir / unique_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    mime_type = file.content_type or "image/jpeg"
    analysis = await openai_service.analyze_image(content, mime_type, persona, platform)

    asset = MediaAsset(
        filename=unique_name,
        original_filename=file.filename or "upload",
        file_path=str(file_path.resolve()),
        mime_type=mime_type,
        file_size_bytes=len(content),
        vision_analysis=analysis.get("description", ""),
        generated_caption=analysis.get("caption", ""),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
