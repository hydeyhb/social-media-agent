import asyncio
import httpx
from datetime import datetime, timezone, timedelta

THREADS_BASE = "https://graph.threads.net/v1.0"


async def exchange_code_for_token(code: str, app_id: str, app_secret: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://graph.threads.net/oauth/access_token",
            data={
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def exchange_for_long_lived_token(short_token: str, app_secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{THREADS_BASE}/access_token",
            params={
                "grant_type": "th_exchange_token",
                "client_secret": app_secret,
                "access_token": short_token,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_long_lived_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{THREADS_BASE}/refresh_access_token",
            params={
                "grant_type": "th_refresh_token",
                "access_token": token,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_user_id(token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{THREADS_BASE}/me",
            params={"fields": "id,username", "access_token": token},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def create_text_container(content: str, user_id: str, token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{THREADS_BASE}/{user_id}/threads",
            data={
                "media_type": "TEXT",
                "text": content,
                "access_token": token,
            },
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def create_image_container(
    image_url: str,
    caption: str,
    user_id: str,
    token: str,
) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{THREADS_BASE}/{user_id}/threads",
            data={
                "media_type": "IMAGE",
                "image_url": image_url,
                "text": caption,
                "access_token": token,
            },
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def create_reply_container(
    content: str,
    reply_to_id: str,
    user_id: str,
    token: str,
) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{THREADS_BASE}/{user_id}/threads",
            data={
                "media_type": "TEXT",
                "text": content,
                "reply_to_id": reply_to_id,
                "access_token": token,
            },
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def publish_container(container_id: str, user_id: str, token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{THREADS_BASE}/{user_id}/threads_publish",
            data={"creation_id": container_id, "access_token": token},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def publish_thread_series(
    segments: list[str],
    user_id: str,
    token: str,
) -> list[str]:
    """Publish a list of text segments as a chained Thread series."""
    published_ids = []
    prev_id = None
    for segment in segments:
        if prev_id is None:
            container_id = await create_text_container(segment, user_id, token)
        else:
            container_id = await create_reply_container(segment, prev_id, user_id, token)
        thread_id = await publish_container(container_id, user_id, token)
        published_ids.append(thread_id)
        prev_id = thread_id
        await asyncio.sleep(2)  # Avoid rate limits
    return published_ids


async def get_thread_metrics(thread_id: str, token: str) -> dict:
    fields = "id,text,like_count,replies_count,repost_count,views,timestamp"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{THREADS_BASE}/{thread_id}",
            params={"fields": fields, "access_token": token},
        )
        if resp.status_code != 200:
            return {}
        return resp.json()


async def get_replies(thread_id: str, token: str) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{THREADS_BASE}/{thread_id}/replies",
            params={
                "fields": "id,text,username,timestamp",
                "access_token": token,
            },
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])
