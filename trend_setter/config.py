"""Application configuration loaded from environment variables / .env."""

from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the trend-setter pipeline.

    Values are loaded from environment variables (or a `.env` file in the
    working directory). Required fields raise a validation error if unset.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Instagram Graph API
    instagram_access_token: str
    instagram_account_id: str

    # Google AI Studio (Gemini)
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-001"

    # Kling AI (video generation)
    kling_api_key: str
    kling_api_base: str = "https://api.klingai.com"
    kling_clip_duration: int = 5  # seconds per clip; 5 or 10 supported
    kling_clips_per_video: int = 6  # 6 x 5s = 30s total

    # OpenAI (TTS voiceover)
    openai_api_key: str

    # Video output
    video_output_dir: str = "output"

    # Perplexity Sonar (research)
    perplexity_api_key: str

    # YouTube Data API v3
    youtube_api_key: str

    # NewsData.io
    newsdataio_api_key: str

    # Google Trends (no key needed — pytrends uses unofficial scraping)
    google_trends_geo: str = "US"

    # Pipeline config
    trend_categories: Annotated[list[str], NoDecode] = [
        "education",
        "science",
        "technology",
        "history",
    ]
    post_interval_hours: int = 6
    max_trends_to_fetch: int = 10

    @field_validator("trend_categories", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        """Allow list fields to be set as a comma-separated env string."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
