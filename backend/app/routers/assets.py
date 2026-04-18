import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import MediaAsset
from app.models.brand import BrandPersona
from app.services.vision_service import process_upload, process_uploads

router = APIRouter()


@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    platform: str = "both",
    persona_id: int = None,
    provider: str = "openai",
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    if persona_id:
        persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
    else:
        persona = db.query(BrandPersona).filter(BrandPersona.is_active == True).first()

    if not persona:
        raise HTTPException(status_code=400, detail="No brand persona configured")

    asset = await process_upload(file, persona, db, platform, provider)
    return {
        "id": asset.id,
        "filename": asset.filename,
        "original_filename": asset.original_filename,
        "mime_type": asset.mime_type,
        "file_size_bytes": asset.file_size_bytes,
        "vision_analysis": asset.vision_analysis,
        "generated_caption": asset.generated_caption,
    }


MAX_MULTI_IMAGES = 6


@router.post("/upload-multi")
async def upload_assets(
    files: List[UploadFile] = File(...),
    platform: str = "both",
    persona_id: int = None,
    provider: str = "openai",
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > MAX_MULTI_IMAGES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_MULTI_IMAGES} images per upload")
    for f in files:
        if not f.content_type or not f.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{f.filename}: only image files supported")

    if persona_id:
        persona = db.query(BrandPersona).filter(BrandPersona.id == persona_id).first()
    else:
        persona = db.query(BrandPersona).filter(BrandPersona.is_active == True).first()
    if not persona:
        raise HTTPException(status_code=400, detail="No brand persona configured")

    result = await process_uploads(files, persona, db, platform, provider)
    return {
        "asset_ids": result["asset_ids"],
        "primary_asset_id": result["primary_asset_id"],
        "description": result["description"],
        "caption": result["caption"],
        "assets": [
            {
                "id": a.id,
                "filename": a.filename,
                "url": f"/uploads/{a.filename}",
                "mime_type": a.mime_type,
                "file_size_bytes": a.file_size_bytes,
            }
            for a in result["assets"]
        ],
    }


@router.get("")
async def list_assets(db: Session = Depends(get_db)):
    assets = db.query(MediaAsset).order_by(MediaAsset.created_at.desc()).all()
    return assets


@router.get("/{asset_id}")
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        if os.path.exists(asset.file_path):
            os.remove(asset.file_path)
    except Exception:
        pass
    db.delete(asset)
    db.commit()
    return {"message": "Deleted"}
