from sqlalchemy.orm import Session

from app.models.analytics import PostAnalytics, PostingTimeStat
from app.models.brand import BrandPersona
from app.models.post import Post
from app.services import openai_service


async def get_content_patterns(db: Session, platform: str = "both") -> dict:
    q = db.query(PostAnalytics)
    if platform != "both":
        q = q.filter(PostAnalytics.platform == platform)
    all_analytics = q.order_by(PostAnalytics.engagement_rate.desc()).all()

    if len(all_analytics) < 4:
        return {"patterns": [], "recommendations": ["數據量不足，請先累積更多貼文表現"], "avoid": []}

    cutoff = max(1, int(len(all_analytics) * 0.2))
    top = all_analytics[:cutoff]
    bottom = all_analytics[-cutoff:]

    def enrich(analytics_list):
        result = []
        for a in analytics_list:
            post = db.query(Post).filter(Post.id == a.post_id).first()
            result.append({
                "content": post.content[:300] if post else "",
                "platform": a.platform,
                "likes": a.likes,
                "comments": a.comments,
                "shares": a.shares,
                "impressions": a.impressions,
                "engagement_rate": a.engagement_rate,
            })
        return result

    return await openai_service.analyze_performance_patterns(enrich(top), enrich(bottom))


async def get_post_improvement(post_id: int, persona: BrandPersona, db: Session) -> dict:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return {"rewritten": "", "explanation": "貼文不存在"}

    analytics = db.query(PostAnalytics).filter(PostAnalytics.post_id == post_id).first()
    perf_data = {}
    if analytics:
        perf_data = {
            "likes": analytics.likes,
            "comments": analytics.comments,
            "shares": analytics.shares,
            "impressions": analytics.impressions,
            "engagement_rate": analytics.engagement_rate,
        }

    return await openai_service.suggest_improvements(post.content, perf_data, persona)


def get_best_posting_windows(db: Session, platform: str, top_n: int = 5) -> list[dict]:
    q = db.query(PostingTimeStat)
    if platform != "both":
        q = q.filter(PostingTimeStat.platform == platform)
    rows = q.filter(PostingTimeStat.sample_count >= 1).order_by(
        PostingTimeStat.avg_engagement_rate.desc()
    ).limit(top_n).all()

    day_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    return [
        {
            "platform": r.platform,
            "day_of_week": r.day_of_week,
            "day_name": day_names[r.day_of_week],
            "hour_of_day": r.hour_of_day,
            "time_label": f"{r.hour_of_day:02d}:00–{r.hour_of_day:02d}:59",
            "avg_engagement_rate": r.avg_engagement_rate,
            "sample_count": r.sample_count,
        }
        for r in rows
    ]
