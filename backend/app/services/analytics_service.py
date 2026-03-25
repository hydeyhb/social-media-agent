from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analytics import EngagementSnapshot, PostAnalytics, PostingTimeStat
from app.models.post import Post
from app.services import facebook_service, threads_service
from app.services.token_service import get_decrypted_access_token


def _engagement_rate(likes: int, comments: int, shares: int, impressions: int) -> float:
    if impressions == 0:
        return 0.0
    return round((likes + comments + shares) / impressions * 100, 4)


async def sync_post_metrics(post: Post, db: Session) -> None:
    platforms = ["facebook", "threads"] if post.platform == "both" else [post.platform]

    for platform in platforms:
        token = get_decrypted_access_token(db, platform)
        if not token:
            continue

        metrics = {}
        if platform == "facebook" and post.facebook_post_id:
            metrics_raw = await facebook_service.get_post_insights(post.facebook_post_id, token)
            reactions = metrics_raw.get("post_reactions_by_type_total", {})
            likes = sum(reactions.values()) if isinstance(reactions, dict) else 0
            metrics = {
                "impressions": metrics_raw.get("post_impressions", 0),
                "reach": metrics_raw.get("post_impressions_unique", 0),
                "likes": likes,
                "comments": metrics_raw.get("post_comments", 0),
                "shares": metrics_raw.get("post_shares", {}).get("count", 0) if isinstance(metrics_raw.get("post_shares"), dict) else 0,
                "clicks": metrics_raw.get("post_clicks", 0),
            }
        elif platform == "threads" and post.threads_post_id:
            data = await threads_service.get_thread_metrics(post.threads_post_id, token)
            metrics = {
                "impressions": data.get("views", 0),
                "reach": data.get("views", 0),
                "likes": data.get("like_count", 0),
                "comments": data.get("replies_count", 0),
                "shares": data.get("repost_count", 0),
                "clicks": 0,
            }

        if not metrics:
            continue

        engagement = _engagement_rate(
            metrics["likes"], metrics["comments"], metrics["shares"], metrics["impressions"]
        )

        existing = db.query(PostAnalytics).filter(
            PostAnalytics.post_id == post.id,
            PostAnalytics.platform == platform,
        ).first()

        if existing:
            for k, v in metrics.items():
                setattr(existing, k, v)
            existing.engagement_rate = engagement
            existing.synced_at = datetime.now(timezone.utc)
        else:
            db.add(PostAnalytics(
                post_id=post.id,
                platform=platform,
                engagement_rate=engagement,
                synced_at=datetime.now(timezone.utc),
                **metrics,
            ))

        # Store snapshot
        db.add(EngagementSnapshot(
            post_id=post.id,
            platform=platform,
            snapshot_at=datetime.now(timezone.utc),
            likes=metrics["likes"],
            comments=metrics["comments"],
            shares=metrics["shares"],
            impressions=metrics["impressions"],
        ))

    db.commit()


async def sync_all_published(db: Session) -> int:
    posts = db.query(Post).filter(Post.status == "published").all()
    count = 0
    for post in posts:
        try:
            await sync_post_metrics(post, db)
            count += 1
        except Exception as e:
            print(f"Failed to sync post {post.id}: {e}")
    return count


def compute_posting_time_stats(db: Session) -> None:
    platforms = ["facebook", "threads"]
    for platform in platforms:
        rows = (
            db.query(Post, PostAnalytics)
            .join(PostAnalytics, Post.id == PostAnalytics.post_id)
            .filter(
                Post.status == "published",
                Post.published_at.isnot(None),
                PostAnalytics.platform == platform,
            )
            .all()
        )

        buckets: dict[tuple, list] = {}
        for post, analytics in rows:
            pub = post.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            key = (pub.weekday(), pub.hour)
            buckets.setdefault(key, []).append(analytics.engagement_rate)

        for (dow, hour), rates in buckets.items():
            avg = round(sum(rates) / len(rates), 4)
            existing = db.query(PostingTimeStat).filter(
                PostingTimeStat.platform == platform,
                PostingTimeStat.day_of_week == dow,
                PostingTimeStat.hour_of_day == hour,
            ).first()
            if existing:
                existing.avg_engagement_rate = avg
                existing.sample_count = len(rates)
                existing.last_computed_at = datetime.now(timezone.utc)
            else:
                db.add(PostingTimeStat(
                    platform=platform,
                    day_of_week=dow,
                    hour_of_day=hour,
                    avg_engagement_rate=avg,
                    sample_count=len(rates),
                ))
    db.commit()


def get_top_performers(db: Session, limit: int = 10, platform: Optional[str] = None) -> list:
    q = db.query(PostAnalytics)
    if platform:
        q = q.filter(PostAnalytics.platform == platform)
    return q.order_by(PostAnalytics.engagement_rate.desc()).limit(limit).all()


def get_overview(db: Session, platform: Optional[str] = None) -> dict:
    q = db.query(PostAnalytics)
    if platform:
        q = q.filter(PostAnalytics.platform == platform)
    rows = q.all()
    if not rows:
        return {"impressions": 0, "likes": 0, "comments": 0, "shares": 0, "avg_engagement_rate": 0.0, "total_posts": 0}
    return {
        "impressions": sum(r.impressions for r in rows),
        "likes": sum(r.likes for r in rows),
        "comments": sum(r.comments for r in rows),
        "shares": sum(r.shares for r in rows),
        "avg_engagement_rate": round(sum(r.engagement_rate for r in rows) / len(rows), 4),
        "total_posts": len(rows),
    }
