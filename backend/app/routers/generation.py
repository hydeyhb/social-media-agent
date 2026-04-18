import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.brand import BrandPersona
from app.models.post import Post
from app.schemas.generation import (
    GenerateBulkRequest,
    GenerateCaptionRequest,
    GenerateSingleRequest,
    GenerateThreadRequest,
)
from app.services import ai_provider, image_gen_service, openai_service, optimization_service

router = APIRouter()


def _get_persona(persona_id: Optional[int], db: Session) -> BrandPersona:
    if persona_id:
        persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
        if persona:
            return persona
    persona = db.query(BrandPersona).filter(BrandPersona.is_active == True).first()
    if not persona:
        raise HTTPException(
            status_code=400,
            detail="No active brand persona. Please configure one in Brand Settings first."
        )
    return persona


@router.post("/single")
async def generate_single(data: GenerateSingleRequest, db: Session = Depends(get_db)):
    persona = _get_persona(data.persona_id, db)
    impl = ai_provider.get(data.provider)
    try:
        content = await impl.generate_post(data.topic, persona, data.platform, data.extra_instructions)
    except Exception as e:
        logger.exception(f"{data.provider} 生文失敗")
        raise HTTPException(status_code=500, detail=f"{data.provider} 生文失敗：{e}")
    image = None
    if data.with_image:
        image = await image_gen_service.generate_for_caption(content, persona, db, data.provider)
    return {"content": content, "persona_id": persona.id, "image": image, "provider": data.provider}


@router.post("/bulk")
async def generate_bulk(data: GenerateBulkRequest, db: Session = Depends(get_db)):
    persona = _get_persona(data.persona_id, db)
    with_image = data.with_image
    impl = ai_provider.get(data.provider)

    async def event_stream():
        for idx, topic in enumerate(data.topics):
            try:
                content = await impl.generate_post(topic, persona, data.platform)
            except Exception as e:
                logger.exception(f"批量生成第 {idx+1} 篇失敗")
                error_payload = json.dumps(
                    {"index": idx, "error": f"生成失敗：{e}", "total": len(data.topics)},
                    ensure_ascii=False,
                )
                yield f"data: {error_payload}\n\n"
                continue
            payload = json.dumps(
                {"index": idx, "content": content, "total": len(data.topics)},
                ensure_ascii=False,
            )
            yield f"data: {payload}\n\n"
            if with_image:
                image = await image_gen_service.generate_for_caption(content, persona, db, data.provider)
                img_payload = json.dumps(
                    {"index": idx, "image": image, "total": len(data.topics)},
                    ensure_ascii=False,
                )
                yield f"data: {img_payload}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/thread")
async def generate_thread(data: GenerateThreadRequest, db: Session = Depends(get_db)):
    persona = _get_persona(data.persona_id, db)
    segments = await openai_service.split_into_thread(
        data.article, persona, data.platform, data.max_chars_per_segment
    )
    group_id = str(uuid.uuid4())
    return {
        "thread_group_id": group_id,
        "platform": data.platform,
        "segments": segments,
        "count": len(segments),
    }


@router.post("/caption")
async def generate_caption(data: GenerateCaptionRequest, db: Session = Depends(get_db)):
    from app.models.asset import MediaAsset
    from app.services.openai_service import analyze_image

    asset = db.query(MediaAsset).filter(MediaAsset.id == data.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    persona = _get_persona(data.persona_id, db)
    with open(asset.file_path, "rb") as f:
        image_bytes = f.read()

    result = await analyze_image(image_bytes, asset.mime_type, persona, data.platform)
    asset.vision_analysis = result.get("description", "")
    asset.generated_caption = result.get("caption", "")
    db.commit()
    return result


@router.post("/optimize/{post_id}")
async def optimize_post(post_id: int, db: Session = Depends(get_db)):
    persona = _get_persona(None, db)
    result = await optimization_service.get_post_improvement(post_id, persona, db)
    return result


@router.post("/optimal-times")
async def optimal_times(platform: str = "both", narrate: bool = True, db: Session = Depends(get_db)):
    windows = optimization_service.get_best_posting_windows(db, platform)
    narration = ""
    if narrate and windows:
        narration = await openai_service.narrate_optimal_times(windows)
    return {"windows": windows, "narration": narration}


@router.post("/patterns")
async def content_patterns(platform: str = "both", db: Session = Depends(get_db)):
    patterns = await optimization_service.get_content_patterns(db, platform)
    return patterns
