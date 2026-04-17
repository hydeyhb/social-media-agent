import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.asset import MediaAsset
from app.models.brand import BrandPersona
from app.services import openai_service

settings = get_settings()


async def generate_for_caption(
    caption: str,
    persona: BrandPersona,
    db: Session,
) -> Optional[dict]:
    """Generate an image to accompany the given caption.

    Returns {"asset_id", "url", "prompt", "model"} or None on failure.
    Failures are swallowed so caption generation isn't blocked.
    """
    try:
        prompt = await openai_service.build_image_prompt(caption, persona)
        image_bytes, model_used = await openai_service.generate_image(prompt)
    except Exception as e:
        return {"error": str(e)}

    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    file_path = uploads_dir / filename
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    asset = MediaAsset(
        filename=filename,
        original_filename=f"ai-generated-{model_used}.png",
        file_path=str(file_path.resolve()),
        mime_type="image/png",
        file_size_bytes=len(image_bytes),
        vision_analysis=prompt,
        generated_caption=caption,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {
        "asset_id": asset.id,
        "url": f"/uploads/{filename}",
        "prompt": prompt,
        "model": model_used,
    }
