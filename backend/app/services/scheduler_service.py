from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.config import get_settings

settings = get_settings()

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.database_url)
        }
        executors = {"default": AsyncIOExecutor()}
        _scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults={"coalesce": True, "max_instances": 1},
            timezone="UTC",
        )
    return _scheduler


def schedule_post(post_id: int, publish_at: datetime) -> str:
    from app.tasks.publish_task import publish_post_task
    scheduler = get_scheduler()
    job_id = f"post_{post_id}"
    scheduler.add_job(
        publish_post_task,
        trigger="date",
        run_date=publish_at,
        args=[post_id],
        id=job_id,
        replace_existing=True,
    )
    return job_id


def cancel_post(job_id: str) -> bool:
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        return True
    except Exception:
        return False


def reschedule_post(job_id: str, new_time: datetime) -> bool:
    scheduler = get_scheduler()
    try:
        scheduler.reschedule_job(job_id, trigger="date", run_date=new_time)
        return True
    except Exception:
        return False


def schedule_token_refresh(token_id: int, refresh_at: datetime, platform: str) -> str:
    from app.tasks.token_refresh_task import refresh_token_task
    scheduler = get_scheduler()
    job_id = f"token_refresh_{platform}_{token_id}"
    scheduler.add_job(
        refresh_token_task,
        trigger="date",
        run_date=refresh_at,
        args=[token_id, platform],
        id=job_id,
        replace_existing=True,
    )
    return job_id
