import asyncio
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.post import Post
from app.services import facebook_service, threads_service
from app.services.token_service import get_active_token, get_decrypted_access_token


async def _publish_to_facebook(post: Post, db) -> str:
    token = get_decrypted_access_token(db, "facebook")
    if not token:
        raise RuntimeError("Facebook token not configured")

    fb_token_record = get_active_token(db, "facebook")
    page_id = fb_token_record.page_id if fb_token_record else ""

    if post.media_asset_id:
        from app.models.asset import MediaAsset
        asset = db.query(MediaAsset).filter(MediaAsset.id == post.media_asset_id).first()
        if asset and asset.file_path:
            post_id, _ = await facebook_service.publish_photo(
                asset.file_path, post.content, page_id, token
            )
            return post_id

    return await facebook_service.publish_post(post.content, page_id, token)


async def _publish_to_threads(post: Post, db) -> str:
    token = get_decrypted_access_token(db, "threads")
    if not token:
        raise RuntimeError("Threads token not configured")

    threads_record = get_active_token(db, "threads")
    user_id = threads_record.user_id if threads_record else ""

    if post.media_asset_id:
        from app.models.asset import MediaAsset
        from app.config import get_settings
        settings = get_settings()
        asset = db.query(MediaAsset).filter(MediaAsset.id == post.media_asset_id).first()
        if asset:
            image_url = f"{settings.frontend_url}/uploads/{asset.filename}"
            container_id = await threads_service.create_image_container(
                image_url, post.content, user_id, token
            )
            return await threads_service.publish_container(container_id, user_id, token)

    container_id = await threads_service.create_text_container(post.content, user_id, token)
    return await threads_service.publish_container(container_id, user_id, token)


async def publish_post_task(post_id: int) -> None:
    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post or post.status not in ("scheduled", "draft"):
            return

        errors = []
        fb_id = ""
        threads_id = ""

        if post.platform in ("facebook", "both"):
            try:
                fb_id = await _publish_to_facebook(post, db)
            except Exception as e:
                errors.append(f"Facebook: {e}")

        if post.platform in ("threads", "both"):
            try:
                threads_id = await _publish_to_threads(post, db)
            except Exception as e:
                errors.append(f"Threads: {e}")

        post.published_at = datetime.now(timezone.utc)
        post.facebook_post_id = fb_id
        post.threads_post_id = threads_id
        post.status = "failed" if errors else "published"
        post.error_message = " | ".join(errors)
        db.commit()
    finally:
        db.close()


def publish_post_task_sync(post_id: int) -> None:
    """Sync wrapper for APScheduler (non-async schedulers)."""
    asyncio.run(publish_post_task(post_id))
