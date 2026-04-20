"""Thin dispatcher: route AI calls to OpenAI or Gemini based on provider name.

Both modules expose the same async public functions used by image_gen_service,
vision_service, and the generation router:
  - generate_post(topic, persona, platform, extra="")
  - analyze_images(images, persona, platform)
  - analyze_image(image_bytes, mime_type, persona, platform)
  - build_image_prompt(caption, persona)
  - generate_image(prompt, size="1024x1024") -> (bytes, model_used)
  - split_into_thread(article, persona, platform, max_chars)
"""
from app.services import gemini_service, openai_service


class _GeminiWithModel:
    """Wraps gemini_service but overrides the text generation model."""

    def __init__(self, text_model: str):
        self._text_model = text_model

    async def generate_post(self, topic, persona, platform="both", extra=""):
        from app.utils.prompt_builder import build_system_prompt
        system = build_system_prompt(persona, platform)
        user_msg = f"請為以下主題撰寫一篇社群貼文：\n{topic}"
        if extra:
            user_msg += f"\n\n額外要求：{extra}"
        return await gemini_service._generate_text(self._text_model, system, user_msg, max_tokens=800, temperature=0.8)

    async def analyze_images(self, images, persona, platform="both"):
        return await gemini_service.analyze_images(images, persona, platform)

    async def analyze_image(self, image_bytes, mime_type, persona, platform="both"):
        return await gemini_service.analyze_image(image_bytes, mime_type, persona, platform)

    async def build_image_prompt(self, caption, persona):
        return await gemini_service.build_image_prompt(caption, persona)

    async def generate_image(self, prompt, size="1024x1024"):
        return await gemini_service.generate_image(prompt, size)

    async def split_into_thread(self, article, persona, platform, max_chars):
        return await gemini_service.split_into_thread(article, persona, platform, max_chars)

    async def generate_persona_from_brief(self, brief):
        return await gemini_service.generate_persona_from_brief(brief)


PROVIDERS = {
    "openai": openai_service,
    "gemini": gemini_service,
    "gemini-flash": _GeminiWithModel("gemini-2.0-flash"),
}

DEFAULT_PROVIDER = "openai"


def get(name: str | None):
    return PROVIDERS.get((name or "").lower(), PROVIDERS[DEFAULT_PROVIDER])
