import json

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

VALID_TONES = {
    "professional", "playful", "authoritative", "warm",
    "inspirational", "casual", "luxurious",
}
VALID_EMOJI = {"none", "moderate", "heavy"}
VALID_LENGTH = {"short", "medium", "long"}


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)


def _sanitize(raw: dict) -> dict:
    """Coerce GPT output into a valid BrandPersonaCreate-shaped dict."""
    out = {
        "name": str(raw.get("name") or "").strip()[:255] or "未命名品牌",
        "tone": raw.get("tone") if raw.get("tone") in VALID_TONES else "professional",
        "style_notes": str(raw.get("style_notes") or "").strip(),
        "target_audience": str(raw.get("target_audience") or "").strip(),
        "emoji_usage": raw.get("emoji_usage") if raw.get("emoji_usage") in VALID_EMOJI else "moderate",
        "post_length_preference": raw.get("post_length_preference") if raw.get("post_length_preference") in VALID_LENGTH else "medium",
    }

    def _to_str_list(v):
        if not isinstance(v, list):
            return []
        return [str(x).strip() for x in v if str(x).strip()][:20]

    out["keywords"] = _to_str_list(raw.get("keywords"))
    out["avoid_phrases"] = _to_str_list(raw.get("avoid_phrases"))
    return out


async def generate_from_brief(brief: str, provider: str = "openai") -> dict:
    if not brief or not brief.strip():
        raise ValueError("brief is required")

    if provider == "gemini":
        from app.services import gemini_service
        raw = await gemini_service.generate_persona_from_brief(brief)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {}
        return _sanitize(parsed)

    client = _client()
    system = (
        "你是品牌人設策略顧問。使用者給你一段品牌簡介，請輸出一份適合社群媒體經營的完整品牌人設。"
        "必須以**嚴格 JSON**回傳，不要 markdown、不要任何說明文字。\n\n"
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
        "規則：\n"
        "- tone / emoji_usage / post_length_preference 必須是上述列舉值之一，不可自創。\n"
        "- keywords 與 avoid_phrases 必須是字串陣列，不可為單一字串或空白。\n"
        "- 所有文字使用繁體中文。\n"
        "- 若簡介資訊不足，依產業常識合理推論，不要問問題。"
    )
    user = f"品牌簡介：\n{brief.strip()}\n\n請輸出 JSON。"

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=900,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return _sanitize(parsed)
