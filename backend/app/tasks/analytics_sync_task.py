import asyncio

from app.database import SessionLocal
from app.services.analytics_service import compute_posting_time_stats, sync_all_published


async def run_analytics_sync() -> None:
    db = SessionLocal()
    try:
        count = await sync_all_published(db)
        compute_posting_time_stats(db)
        print(f"[Analytics Sync] Synced {count} posts.")
    finally:
        db.close()


def run_analytics_sync_sync() -> None:
    asyncio.run(run_analytics_sync())
