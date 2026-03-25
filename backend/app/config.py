from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""

    # Facebook
    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_redirect_uri: str = "http://localhost:8000/api/auth/facebook/callback"

    # Threads
    threads_app_id: str = ""
    threads_app_secret: str = ""
    threads_redirect_uri: str = "http://localhost:8000/api/auth/threads/callback"

    # Security
    token_encryption_key: str = ""
    secret_key: str = "change-me-in-production"

    # App
    database_url: str = "sqlite:///./social_agent.db"
    uploads_dir: str = "./uploads"
    frontend_url: str = "http://localhost:5173"

    # Facebook webhook
    facebook_webhook_verify_token: str = "my_webhook_verify_token"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
