import base64
import json
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.brand import BrandPersona
from app.utils.prompt_builder import build_system_prompt, build_thread_split_prompt

settings = get_settings()


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _get_char_limit(persona: BrandPersona) -> int:
    mapping = {"short": 100, "medium": 200, "long": 400}
    return mapping.get(persona.post_length_preference or "medium", 200)


async def generate_post(
    topic: str,
    persona: BrandPersona,
    platform: str = "both",
    extra: str = "",
) -> str:
    client = _client()
    system = build_system_prompt(persona, platform)
    user_msg = f"請為以下主題撰寫一篇社群貼文：\n{topic}"
    if extra:
        user_msg += f"\n\n額外要求：{extra}"

    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=800,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()


async def generate_bulk_posts(
    topics: list[str],
    persona: BrandPersona,
    platform: str = "both",
) -> AsyncGenerator[str, None]:
    for topic in topics:
        content = await generate_post(topic, persona, platform)
        yield content


async def analyze_image(
    image_bytes: bytes,
    mime_type: str,
    persona: BrandPersona,
    platform: str = "both",
) -> dict:
    client = _client()
    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{b64}"

    system = build_system_prompt(persona, platform)
    char_limit = _get_char_limit(persona)

    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {
                        "type": "text",
                        "text": (
                            f"請分析這張產品圖片，並以 JSON 格式回傳以下三個欄位：\n"
                            f"1. description：圖片內容的客觀描述（中文，100字內）\n"
                            f"2. caption：符合品牌風格的社群文案（中文，{char_limit}字內，含適當 emoji）\n"
                            f"3. hashtags：5個相關 hashtag 的陣列\n"
                            f"只回傳 JSON，不要其他說明文字。"
                        ),
                    },
                ],
            },
        ],
        max_tokens=800,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return {"description": raw, "caption": raw, "hashtags": []}


async def split_into_thread(
    article: str,
    persona: BrandPersona,
    platform: str = "threads",
    max_chars: int = 500,
) -> list[str]:
    client = _client()
    system = build_system_prompt(persona, platform)
    user_msg = build_thread_split_prompt(article, platform, max_chars)

    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=3000,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        segments = json.loads(raw)
        return [s.strip() for s in segments if s.strip()]
    except Exception:
        # Fallback: split by double newline
        return [p.strip() for p in raw.split("\n\n") if p.strip()]


async def analyze_performance_patterns(
    top_posts: list[dict],
    bottom_posts: list[dict],
) -> dict:
    client = _client()
    prompt = (
        f"以下是社群貼文的表現分析任務。\n\n"
        f"【高表現貼文（互動率前20%）】\n{json.dumps(top_posts, ensure_ascii=False, indent=2)}\n\n"
        f"【低表現貼文（互動率後20%）】\n{json.dumps(bottom_posts, ensure_ascii=False, indent=2)}\n\n"
        f"請分析高低表現貼文的差異，以 JSON 格式回傳：\n"
        f'{{"patterns": ["高表現規律1", ...], "recommendations": ["建議1", ...], "avoid": ["要避免的1", ...]}}\n'
        f"只回傳 JSON。"
    )
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.5,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return {"patterns": [], "recommendations": [raw], "avoid": []}


async def suggest_improvements(
    post_content: str,
    performance_data: dict,
    persona: BrandPersona,
) -> dict:
    client = _client()
    system = build_system_prompt(persona, "both")
    prompt = (
        f"以下這篇貼文的互動表現偏低：\n\n"
        f"【原始貼文】\n{post_content}\n\n"
        f"【表現數據】\n{json.dumps(performance_data, ensure_ascii=False)}\n\n"
        f"請根據品牌風格，提供一個改進版本，並說明改動原因。\n"
        f"以 JSON 格式回傳：\n"
        f'{{"rewritten": "改進後的貼文內容", "explanation": "改動說明"}}\n'
        f"只回傳 JSON。"
    )
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=800,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except Exception:
        return {"rewritten": raw, "explanation": ""}


async def narrate_optimal_times(heatmap_data: list[dict]) -> str:
    client = _client()
    prompt = (
        f"以下是社群帳號各時段的平均互動率數據：\n{json.dumps(heatmap_data, ensure_ascii=False)}\n\n"
        f"請用繁體中文，以2–3段自然語言，說明最佳發文時段與應避免的時段，並給出具體建議。"
    )
    resp = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()
