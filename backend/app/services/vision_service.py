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
    result = await process_uploads([file], persona, db, platform)
    return result["assets"][0]


async def process_uploads(
    files: list[UploadFile],
    persona: BrandPersona,
    db: Session,
    platform: str = "both",
) -> dict:
    if not files:
        raise ValueError("files must not be empty")

    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    saved = []  # list of (path, filename, original, mime, size, content)
    for file in files:
        ext = Path(file.filename or "").suffix or ".jpg"
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = uploads_dir / unique_name
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        mime_type = file.content_type or "image/jpeg"
        saved.append({
            "filename": unique_name,
            "original_filename": file.filename or "upload",
            "file_path": str(file_path.resolve()),
            "mime_type": mime_type,
            "size": len(content),
            "content": content,
        })

    images = [(s["content"], s["mime_type"]) for s in saved]
    analysis = await openai_service.analyze_images(images, persona, platform)
    description = analysis.get("description", "")
    caption = analysis.get("caption", "")

    assets: list[MediaAsset] = []
    for idx, s in enumerate(saved):
        asset = MediaAsset(
            filename=s["filename"],
            original_filename=s["original_filename"],
            file_path=s["file_path"],
            mime_type=s["mime_type"],
            file_size_bytes=s["size"],
            vision_analysis=description if idx == 0 else "",
            generated_caption=caption if idx == 0 else "",
        )
        db.add(asset)
        assets.append(asset)
    db.commit()
    for a in assets:
        db.refresh(a)

    return {
        "assets": assets,
        "primary_asset_id": assets[0].id,
        "asset_ids": [a.id for a in assets],
        "description": description,
        "caption": caption,
    }
