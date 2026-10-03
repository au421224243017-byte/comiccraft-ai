from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_outline_model: str = "gemini-2.5-flash"
    gemini_story_model: str = "gemini-2.5-flash"

    hf_api_key: str = ""
    hf_image_model: str = "stabilityai/stable-diffusion-xl-base-1.0"

    use_mock_ai: bool = True

    # Image provider: "mock", "cloudflare" or "huggingface".
    # Leave empty to follow USE_MOCK_AI (the old behaviour).
    image_provider: str = ""

    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_image_model: str = "@cf/black-forest-labs/flux-1-schnell"
    cloudflare_image_steps: int = 4

    image_width: int = 768
    image_height: int = 768
    max_prompt_length: int = 2000

    output_dir: Path = BASE_DIR / "static"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()