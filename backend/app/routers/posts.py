from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.schemas.post import PostCreate, PostOut, PostSchedule, PostUpdate
from app.services.scheduler_service import cancel_post, reschedule_post, schedule_post
from app.tasks.publish_task import publish_post_task

router = APIRouter()


@router.get("", response_model=List[PostOut])
async def list_posts(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    q = db.query(Post)
    if status:
        q = q.filter(Post.status == status)
    if platform:
        q = q.filter(Post.platform == platform)
    return q.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=PostOut)
async def create_post(data: PostCreate, db: Session = Depends(get_db)):
    post = Post(
        platform=data.platform,
        content=data.content,
        status="draft",
        scheduled_at=data.scheduled_at,
        media_asset_id=data.media_asset_id,
        brand_persona_id=data.brand_persona_id,
        generation_prompt=data.generation_prompt,
        thread_group_id=data.thread_group_id,
        thread_sequence_order=data.thread_sequence_order,
        is_thread_parent=data.is_thread_parent,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    if data.scheduled_at:
        job_id = schedule_post(post.id, data.scheduled_at)
        post.status = "scheduled"
        post.apscheduler_job_id = job_id
        db.commit()

    return post


@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if data.content is not None:
        post.content = data.content
    if data.platform is not None:
        post.platform = data.platform
    if data.media_asset_id is not None:
        post.media_asset_id = data.media_asset_id
    if data.scheduled_at is not None:
        post.scheduled_at = data.scheduled_at
        if post.apscheduler_job_id:
            reschedule_post(post.apscheduler_job_id, data.scheduled_at)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.apscheduler_job_id:
        cancel_post(post.apscheduler_job_id)
    db.delete(post)
    db.commit()
    return {"message": "Deleted"}


@router.post("/{post_id}/publish-now", response_model=PostOut)
async def publish_now(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await publish_post_task(post_id)
    db.refresh(post)
    return post


@router.post("/{post_id}/schedule", response_model=PostOut)
async def schedule(post_id: int, data: PostSchedule, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.apscheduler_job_id:
        reschedule_post(post.apscheduler_job_id, data.scheduled_at)
    else:
        job_id = schedule_post(post_id, data.scheduled_at)
        post.apscheduler_job_id = job_id
    post.scheduled_at = data.scheduled_at
    post.status = "scheduled"
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/cancel-schedule", response_model=PostOut)
async def cancel_schedule(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.apscheduler_job_id:
        cancel_post(post.apscheduler_job_id)
        post.apscheduler_job_id = ""
    post.status = "draft"
    db.commit()
    db.refresh(post)
    return post


@router.get("/thread/{thread_group_id}", response_model=List[PostOut])
async def get_thread_series(thread_group_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Post)
        .filter(Post.thread_group_id == thread_group_id)
        .order_by(Post.thread_sequence_order)
        .all()
    )
