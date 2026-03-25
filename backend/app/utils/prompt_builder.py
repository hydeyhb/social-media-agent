import json
from app.models.brand import BrandPersona


def build_system_prompt(persona: BrandPersona, platform: str) -> str:
    keywords = json.loads(persona.keywords or "[]")
    avoid = json.loads(persona.avoid_phrases or "[]")
    keywords_str = ", ".join(keywords) if keywords else "（無特定關鍵字）"
    avoid_str = ", ".join(avoid) if avoid else "（無禁用詞）"

    length_map = {
        "short": "50–100 字，簡短有力",
        "medium": "100–200 字，適中詳盡",
        "long": "200–400 字，深度詳細",
    }
    length_guide = length_map.get(persona.post_length_preference or "medium", "100–200 字")

    emoji_map = {
        "none": "完全不使用 emoji",
        "moderate": "適量使用 emoji（1–3 個）點綴文字",
        "heavy": "大量使用 emoji，讓內容更活潑生動",
    }
    emoji_guide = emoji_map.get(persona.emoji_usage or "moderate", "適量使用 emoji")

    platform_guide = {
        "facebook": "Facebook 粉絲專頁貼文，可附加連結預覽，適合較長的故事型內容，需要號召行動（CTA）",
        "threads": "Threads 平台，風格輕鬆對話，500字以內，鼓勵互動與回覆",
        "both": "同時適用 Facebook 與 Threads，內容需兼顧兩平台風格",
    }.get(platform, platform)

    return f"""你是 {persona.name} 的社群媒體專業經理人，負責撰寫所有社群平台內容。

【品牌資訊】
品牌名稱：{persona.name}
口吻風格：{persona.tone}
目標受眾：{persona.target_audience or "一般消費者"}
風格說明：{persona.style_notes or "專業、真誠、貼近品牌價值"}

【內容規則】
- 必須自然融入的關鍵字：{keywords_str}
- 絕對不能出現的詞語：{avoid_str}
- Emoji 使用原則：{emoji_guide}
- 文字長度：{length_guide}
- 發布平台：{platform_guide}

【核心原則】
1. 每篇內容都要展現品牌獨特個性，不能像罐頭文案
2. 用真實、有溫度的語言，彷彿真人在說話
3. 結尾需要有明確的 CTA（號召行動）
4. 避免過度行銷味，讓讀者覺得有價值才願意互動"""


def build_thread_split_prompt(article: str, platform: str, max_chars: int) -> str:
    return f"""請將以下長文拆分為 {platform} 的串文（Thread），每段不超過 {max_chars} 字。

規則：
1. 每段內容獨立完整，可單獨閱讀
2. 第一段必須有吸引人的開場，讓讀者想繼續看
3. 保持敘事的邏輯流暢，段落之間有自然銜接
4. 最後一段要有結語或 CTA
5. 不要在每段加上「第X段」等標記
6. 回傳格式：純 JSON 陣列，例如 ["段落1", "段落2", ...]

長文內容：
{article}"""
