import httpx
from typing import Optional

GRAPH_BASE = "https://graph.facebook.com/v19.0"


async def publish_post(content: str, page_id: str, page_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_BASE}/{page_id}/feed",
            data={"message": content, "access_token": page_token},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def publish_photo(
    image_path: str,
    caption: str,
    page_id: str,
    page_token: str,
    published: bool = True,
) -> tuple[str, str]:
    """Upload photo then attach to a feed post so it appears in timeline (not Photos album).
    Returns (post_id, photo_id)"""
    async with httpx.AsyncClient() as client:
        # Step 1: upload photo as unpublished to get photo_id
        with open(image_path, "rb") as f:
            resp = await client.post(
                f"{GRAPH_BASE}/{page_id}/photos",
                data={
                    "access_token": page_token,
                    "published": "false",
                },
                files={"source": f},
                timeout=60,
            )
        resp.raise_for_status()
        photo_id = resp.json().get("id", "")

        if not published:
            return "", photo_id

        # Step 2: create a feed post with the photo attached (shows in timeline)
        resp2 = await client.post(
            f"{GRAPH_BASE}/{page_id}/feed",
            data={
                "message": caption,
                "access_token": page_token,
                "attached_media": f'[{{"media_fbid":"{photo_id}"}}]',
            },
            timeout=30,
        )
        resp2.raise_for_status()
        post_id = resp2.json().get("id", "")
        return post_id, photo_id


async def add_comment(post_id: str, message: str, page_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_BASE}/{post_id}/comments",
            data={"message": message, "access_token": page_token},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def reply_to_comment(comment_id: str, message: str, page_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_BASE}/{comment_id}/comments",
            data={"message": message, "access_token": page_token},
        )
        resp.raise_for_status()
        return resp.json().get("id", "")


async def get_post_insights(post_id: str, page_token: str) -> dict:
    metrics = ",".join([
        "post_impressions",
        "post_impressions_unique",
        "post_reactions_by_type_total",
        "post_comments",
        "post_shares",
        "post_clicks",
    ])
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/{post_id}/insights",
            params={"metric": metrics, "access_token": page_token},
        )
        if resp.status_code != 200:
            return {}
        data = resp.json().get("data", [])
    result = {}
    for item in data:
        result[item["name"]] = item.get("values", [{}])[-1].get("value", 0)
    return result


async def exchange_code_for_token(code: str, app_id: str, app_secret: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def exchange_for_long_lived_token(short_token: str, app_id: str, app_secret: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": short_token,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_pages(long_lived_user_token: str) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/me/accounts",
            params={"access_token": long_lived_user_token},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def get_page_comments(post_id: str, page_token: str, limit: int = 25) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}/{post_id}/comments",
            params={
                "fields": "id,message,from,created_time",
                "limit": limit,
                "access_token": page_token,
            },
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("data", [])
