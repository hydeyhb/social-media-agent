import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.brand import BrandPersona
from app.schemas.brand import (
    BrandPersonaCreate,
    BrandPersonaOut,
    BrandPersonaUpdate,
    PersonaBriefRequest,
)
from app.services import persona_service

router = APIRouter()


def _serialize(persona: BrandPersona) -> BrandPersonaOut:
    return BrandPersonaOut(
        id=persona.id,
        name=persona.name,
        tone=persona.tone or "",
        style_notes=persona.style_notes or "",
        target_audience=persona.target_audience or "",
        keywords=json.loads(persona.keywords or "[]"),
        avoid_phrases=json.loads(persona.avoid_phrases or "[]"),
        emoji_usage=persona.emoji_usage or "moderate",
        post_length_preference=persona.post_length_preference or "medium",
        is_active=persona.is_active,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.get("", response_model=BrandPersonaOut)
async def get_active_persona(db: Session = Depends(get_db)):
    persona = db.query(BrandPersona).filter(BrandPersona.is_active == True).first()
    if not persona:
        raise HTTPException(status_code=404, detail="No active brand persona. Please create one.")
    return _serialize(persona)


@router.get("/all", response_model=List[BrandPersonaOut])
async def list_personas(db: Session = Depends(get_db)):
    personas = db.query(BrandPersona).order_by(BrandPersona.created_at.desc()).all()
    return [_serialize(p) for p in personas]


@router.post("", response_model=BrandPersonaOut)
async def create_persona(data: BrandPersonaCreate, db: Session = Depends(get_db)):
    persona = BrandPersona(
        name=data.name,
        tone=data.tone,
        style_notes=data.style_notes,
        target_audience=data.target_audience,
        keywords=json.dumps(data.keywords, ensure_ascii=False),
        avoid_phrases=json.dumps(data.avoid_phrases, ensure_ascii=False),
        emoji_usage=data.emoji_usage,
        post_length_preference=data.post_length_preference,
        is_active=False,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return _serialize(persona)


@router.put("/{persona_id}", response_model=BrandPersonaOut)
async def update_persona(persona_id: int, data: BrandPersonaUpdate, db: Session = Depends(get_db)):
    persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if data.name is not None:
        persona.name = data.name
    if data.tone is not None:
        persona.tone = data.tone
    if data.style_notes is not None:
        persona.style_notes = data.style_notes
    if data.target_audience is not None:
        persona.target_audience = data.target_audience
    if data.keywords is not None:
        persona.keywords = json.dumps(data.keywords, ensure_ascii=False)
    if data.avoid_phrases is not None:
        persona.avoid_phrases = json.dumps(data.avoid_phrases, ensure_ascii=False)
    if data.emoji_usage is not None:
        persona.emoji_usage = data.emoji_usage
    if data.post_length_preference is not None:
        persona.post_length_preference = data.post_length_preference
    db.commit()
    db.refresh(persona)
    return _serialize(persona)


@router.post("/{persona_id}/activate", response_model=BrandPersonaOut)
async def activate_persona(persona_id: int, db: Session = Depends(get_db)):
    db.query(BrandPersona).update({"is_active": False})
    persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    persona.is_active = True
    db.commit()
    db.refresh(persona)
    return _serialize(persona)


@router.post("/generate", response_model=BrandPersonaCreate)
async def generate_persona_from_brief(data: PersonaBriefRequest):
    """Generate suggested brand persona fields from a free-text brief.

    Does NOT write to DB — frontend will let the user edit then POST /brand to save.
    """
    if not data.brief.strip():
        raise HTTPException(status_code=400, detail="brief is required")
    try:
        suggestion = await persona_service.generate_from_brief(data.brief)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 生成失敗：{e}")
    return suggestion


@router.delete("/{persona_id}")
async def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    db.delete(persona)
    db.commit()
    return {"message": "Deleted"}
