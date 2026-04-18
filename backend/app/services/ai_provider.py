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

PROVIDERS = {
    "openai": openai_service,
    "gemini": gemini_service,
}

DEFAULT_PROVIDER = "openai"


def get(name: str | None):
    return PROVIDERS.get((name or "").lower(), PROVIDERS[DEFAULT_PROVIDER])
