import base64
import json
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.brand import BrandPersona
from app.utils.prompt_builder import build_system_prompt, build_thread_split_prompt

settings = get_settings()

IMAGE_MODELS = ["gpt-image-1", "dall-e-3"]


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
        model="gpt-4o-mini",
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


async def analyze_images(
    images: list[tuple[bytes, str]],
    persona: BrandPersona,
    platform: str = "both",
) -> dict:
    if not images:
        raise ValueError("images list must not be empty")
    client = _client()
    system = build_system_prompt(persona, platform)
    char_limit = _get_char_limit(persona)
    n = len(images)

    image_blocks = []
    for image_bytes, mime_type in images:
        b64 = base64.b64encode(image_bytes).decode()
        data_url = f"data:{mime_type};base64,{b64}"
        image_blocks.append({"type": "image_url", "image_url": {"url": data_url}})

    if n == 1:
        text_instruction = (
            f"請分析這張產品圖片，並以 JSON 格式回傳以下三個欄位：\n"
            f"1. description：圖片內容的客觀描述（中文，100字內）\n"
            f"2. caption：符合品牌風格的社群文案（中文，{char_limit}字內，含適當 emoji）\n"
            f"3. hashtags：5個相關 hashtag 的陣列\n"
            f"只回傳 JSON，不要其他說明文字。"
        )
    else:
        text_instruction = (
            f"以上是同一篇貼文要使用的 {n} 張圖片。請綜合這 {n} 張圖一起閱讀，"
            f"產生**一則統整的**社群貼文，並以 JSON 格式回傳以下三個欄位：\n"
            f"1. description：綜合描述這 {n} 張圖呈現的主題或場景（中文，150字內）\n"
            f"2. caption：符合品牌風格的**單則**社群文案，能涵蓋這組圖的整體訊息"
            f"（中文，{char_limit}字內，含適當 emoji）\n"
            f"3. hashtags：5個相關 hashtag 的陣列\n"
            f"只回傳 JSON，不要其他說明文字、不要逐張描述。"
        )

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [*image_blocks, {"type": "text", "text": text_instruction}],
            },
        ],
        max_tokens=900,
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
        return {"description": raw, "caption": raw, "hashtags": []}


async def analyze_image(
    image_bytes: bytes,
    mime_type: str,
    persona: BrandPersona,
    platform: str = "both",
) -> dict:
    return await analyze_images([(image_bytes, mime_type)], persona, platform)


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
        model="gpt-4o-mini",
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
        model="gpt-4o-mini",
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
        model="gpt-4o-mini",
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


async def build_image_prompt(caption: str, persona: BrandPersona) -> str:
    """Convert a Chinese social post into a polished English visual prompt."""
    client = _client()
    tone = persona.tone or "professional"
    style_notes = persona.style_notes or ""
    audience = persona.target_audience or ""

    system = (
        "You are an art director writing prompts for a state-of-the-art image model. "
        "Translate the Chinese social media caption into ONE single English image prompt "
        "(max ~80 words) that will produce a photorealistic, magazine-quality visual. "
        "Always include: subject, composition, lighting, color palette, mood, and lens/style. "
        "Match the brand persona. Strictly forbid any text, letters, captions, watermarks, "
        "or logos in the image. Output only the prompt — no explanations, no quotes, no labels."
    )
    user = (
        f"Brand tone: {tone}\n"
        f"Audience: {audience}\n"
        f"Style notes: {style_notes}\n\n"
        f"Caption:\n{caption}\n\n"
        f"Write the image prompt now."
    )
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=200,
        temperature=0.7,
    )
    prompt = resp.choices[0].message.content.strip().strip('"').strip()
    if "no text" not in prompt.lower():
        prompt += " No text, no letters, no watermark, no logo in the image."
    return prompt


async def generate_image(prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
    """Generate an image, trying gpt-image-1 first then dall-e-3.

    Returns (image_bytes, model_used).
    """
    client = _client()
    last_error: Optional[Exception] = None
    for model in IMAGE_MODELS:
        try:
            kwargs = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1,
            }
            if model == "dall-e-3":
                kwargs["quality"] = "hd"
                kwargs["response_format"] = "b64_json"
            resp = await client.images.generate(**kwargs)
            data = resp.data[0]
            b64 = getattr(data, "b64_json", None)
            if b64:
                return base64.b64decode(b64), model
            url = getattr(data, "url", None)
            if url:
                import httpx
                async with httpx.AsyncClient(timeout=60.0) as http:
                    r = await http.get(url)
                    r.raise_for_status()
                    return r.content, model
            raise RuntimeError(f"{model} returned no image data")
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All image models failed. Last error: {last_error}")


async def narrate_optimal_times(heatmap_data: list[dict]) -> str:
    client = _client()
    prompt = (
        f"以下是社群帳號各時段的平均互動率數據：\n{json.dumps(heatmap_data, ensure_ascii=False)}\n\n"
        f"請用繁體中文，以2–3段自然語言，說明最佳發文時段與應避免的時段，並給出具體建議。"
    )
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()
