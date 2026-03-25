from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analytics import EngagementSnapshot, PostAnalytics, PostingTimeStat
from app.models.post import Post
from app.schemas.analytics import PostAnalyticsOut, PostingTimeStatOut
from app.services.analytics_service import get_overview, get_top_performers, sync_all_published

router = APIRouter()


@router.get("/overview")
async def overview(platform: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return get_overview(db, platform)


@router.get("/posts", response_model=List[PostAnalyticsOut])
async def analytics_per_post(
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(PostAnalytics)
    if platform:
        q = q.filter(PostAnalytics.platform == platform)
    return q.order_by(PostAnalytics.engagement_rate.desc()).limit(limit).all()


@router.get("/posts/{post_id}")
async def post_analytics_detail(post_id: int, db: Session = Depends(get_db)):
    analytics = db.query(PostAnalytics).filter(PostAnalytics.post_id == post_id).all()
    snapshots = (
        db.query(EngagementSnapshot)
        .filter(EngagementSnapshot.post_id == post_id)
        .order_by(EngagementSnapshot.snapshot_at)
        .all()
    )
    return {"analytics": analytics, "snapshots": snapshots}


@router.get("/trends")
async def trends(
    days: int = Query(30, le=365),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)

    q = (
        db.query(
            Post.published_at,
            PostAnalytics.impressions,
            PostAnalytics.likes,
            PostAnalytics.comments,
            PostAnalytics.shares,
            PostAnalytics.engagement_rate,
        )
        .join(PostAnalytics, Post.id == PostAnalytics.post_id)
        .filter(Post.published_at >= since, Post.status == "published")
    )
    if platform:
        q = q.filter(PostAnalytics.platform == platform)

    rows = q.order_by(Post.published_at).all()
    return [
        {
            "date": r[0].isoformat() if r[0] else None,
            "impressions": r[1],
            "likes": r[2],
            "comments": r[3],
            "shares": r[4],
            "engagement_rate": r[5],
        }
        for r in rows
    ]


@router.get("/top-performers")
async def top_performers(
    limit: int = Query(10, le=50),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    top = get_top_performers(db, limit, platform)
    result = []
    for a in top:
        post = db.query(Post).filter(Post.id == a.post_id).first()
        result.append({
            "post_id": a.post_id,
            "content_preview": post.content[:100] if post else "",
            "platform": a.platform,
            "likes": a.likes,
            "comments": a.comments,
            "shares": a.shares,
            "impressions": a.impressions,
            "engagement_rate": a.engagement_rate,
            "published_at": post.published_at.isoformat() if post and post.published_at else None,
        })
    return result


@router.get("/posting-times", response_model=List[PostingTimeStatOut])
async def posting_times(
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(PostingTimeStat)
    if platform:
        q = q.filter(PostingTimeStat.platform == platform)
    return q.all()


@router.post("/sync")
async def sync_analytics(db: Session = Depends(get_db)):
    count = await sync_all_published(db)
    return {"synced": count}
