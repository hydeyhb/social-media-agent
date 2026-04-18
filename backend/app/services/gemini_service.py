"""Google Gemini provider — mirrors openai_service public API.

Models used:
- Text  : gemini-2.5-pro     (高品質文案)
- Vision: gemini-2.5-flash   (cheaper, multimodal)
- Image : imagen-4.0-generate-001 → fallback imagen-3.0-generate-002
"""
import asyncio
import base64
import json
from typing import Optional

from google import genai
from google.genai import types

from app.config import get_settings
from app.models.brand import BrandPersona
from app.utils.prompt_builder import build_system_prompt, build_thread_split_prompt

settings = get_settings()

TEXT_MODEL = "gemini-2.5-pro"
VISION_MODEL = "gemini-2.5-flash"
IMAGE_MODELS = ["imagen-4.0-generate-001", "imagen-3.0-generate-002"]


def _client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY 未設定，請在 backend/.env 填入。")
    return genai.Client(api_key=settings.gemini_api_key)


def _get_char_limit(persona: BrandPersona) -> int:
    mapping = {"short": 100, "medium": 200, "long": 400}
    return mapping.get(persona.post_length_preference or "medium", 200)


def _strip_json_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


async def _generate_text(model: str, system: str, user: str, max_tokens: int = 800, temperature: float = 0.7) -> str:
    client = _client()
    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
    resp = await client.aio.models.generate_content(model=model, contents=user, config=config)
    return (resp.text or "").strip()


async def generate_post(
    topic: str,
    persona: BrandPersona,
    platform: str = "both",
    extra: str = "",
) -> str:
    system = build_system_prompt(persona, platform)
    user_msg = f"請為以下主題撰寫一篇社群貼文：\n{topic}"
    if extra:
        user_msg += f"\n\n額外要求：{extra}"
    return await _generate_text(TEXT_MODEL, system, user_msg, max_tokens=800, temperature=0.8)


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

    image_parts = [types.Part.from_bytes(data=b, mime_type=mt) for b, mt in images]

    if n == 1:
        text_instruction = (
            f"請分析這張產品圖片，並以 JSON 格式回傳以下三個欄位：\n"
            f"1. description：圖片內容的客觀描述（中文，100字內）\n"
            f"2. caption：符合品牌風格的社群文案（中文，{char_limit}字內，含適當 emoji）\n"
            f"3. hashtags：5個相關 hashtag 的陣列\n"
            f"只回傳 JSON。"
        )
    else:
        text_instruction = (
            f"以上是同一篇貼文要使用的 {n} 張圖片。請綜合這 {n} 張圖一起閱讀，"
            f"產生**一則統整的**社群貼文，並以 JSON 格式回傳：\n"
            f"1. description：綜合描述這 {n} 張圖呈現的主題或場景（中文，150字內）\n"
            f"2. caption：符合品牌風格的**單則**社群文案，能涵蓋這組圖的整體訊息"
            f"（中文，{char_limit}字內，含適當 emoji）\n"
            f"3. hashtags：5個相關 hashtag 的陣列\n"
            f"只回傳 JSON、不要逐張描述。"
        )

    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=900,
        temperature=0.7,
        response_mime_type="application/json",
    )
    resp = await client.aio.models.generate_content(
        model=VISION_MODEL,
        contents=[*image_parts, text_instruction],
        config=config,
    )
    raw = _strip_json_fence(resp.text or "")
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
    system = build_system_prompt(persona, platform)
    user_msg = build_thread_split_prompt(article, platform, max_chars)
    raw = await _generate_text(TEXT_MODEL, system, user_msg, max_tokens=3000, temperature=0.7)
    raw = _strip_json_fence(raw)
    try:
        segments = json.loads(raw)
        return [s.strip() for s in segments if s.strip()]
    except Exception:
        return [p.strip() for p in raw.split("\n\n") if p.strip()]


async def build_image_prompt(caption: str, persona: BrandPersona) -> str:
    tone = persona.tone or "professional"
    style_notes = persona.style_notes or ""
    audience = persona.target_audience or ""
    system = (
        "You are an art director writing prompts for a state-of-the-art image model. "
        "Translate the Chinese social caption into ONE single English image prompt "
        "(max ~80 words) producing a photorealistic, magazine-quality visual. "
        "Always include: subject, composition, lighting, color palette, mood, lens/style. "
        "Strictly forbid any text, letters, captions, watermarks, logos in the image. "
        "Output only the prompt — no quotes, no labels."
    )
    user = (
        f"Brand tone: {tone}\nAudience: {audience}\nStyle notes: {style_notes}\n\n"
        f"Caption:\n{caption}\n\nWrite the image prompt now."
    )
    prompt = await _generate_text(TEXT_MODEL, system, user, max_tokens=200, temperature=0.7)
    prompt = prompt.strip().strip('"').strip()
    if "no text" not in prompt.lower():
        prompt += " No text, no letters, no watermark, no logo in the image."
    return prompt


async def generate_persona_from_brief(brief: str) -> str:
    """Return raw JSON string. Sanitization is shared in persona_service."""
    system = (
        "你是品牌人設策略顧問。使用者給你一段品牌簡介，請輸出一份適合社群媒體經營的完整品牌人設。"
        "以**嚴格 JSON**回傳，不要 markdown。\n\n"
        "JSON 結構：\n"
        "{\n"
        '  "name": "品牌名稱字串",\n'
        '  "tone": "professional | playful | authoritative | warm | inspirational | casual | luxurious 其中之一",\n'
        '  "style_notes": "品牌個性、價值觀、溝通風格的繁體中文描述（80-150字）",\n'
        '  "target_audience": "目標受眾繁體中文描述（30-80字）",\n'
        '  "keywords": ["3-8個適合自然融入文案的繁體中文關鍵字"],\n'
        '  "avoid_phrases": ["3-6個品牌應避免的詞語或語氣"],\n'
        '  "emoji_usage": "none | moderate | heavy 其中之一",\n'
        '  "post_length_preference": "short | medium | long 其中之一"\n'
        "}\n\n"
        "規則：tone / emoji_usage / post_length_preference 必須是上述列舉值之一。"
        "keywords 與 avoid_phrases 必須是字串陣列。所有文字使用繁體中文。"
    )
    client = _client()
    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=900,
        temperature=0.7,
        response_mime_type="application/json",
    )
    resp = await client.aio.models.generate_content(
        model=TEXT_MODEL,
        contents=f"品牌簡介：\n{brief.strip()}\n\n請輸出 JSON。",
        config=config,
    )
    return _strip_json_fence(resp.text or "")


async def generate_image(prompt: str, size: str = "1024x1024") -> tuple[bytes, str]:
    """Generate an image via Imagen, with model fallback. Returns (bytes, model_used)."""
    client = _client()
    last_error: Optional[Exception] = None
    for model in IMAGE_MODELS:
        try:
            config = types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
            )
            resp = await client.aio.models.generate_images(
                model=model, prompt=prompt, config=config
            )
            if not resp.generated_images:
                raise RuntimeError(f"{model} returned no images")
            img = resp.generated_images[0].image
            data = getattr(img, "image_bytes", None)
            if data:
                return data, model
            raise RuntimeError(f"{model} returned image without bytes")
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All Gemini image models failed. Last error: {last_error}")
