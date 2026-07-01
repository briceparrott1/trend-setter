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

    # Google Cloud / Vertex AI (Gemini + Veo 2)
    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    gemini_model: str = "gemini-2.0-flash-001"
    veo_model: str = "veo-002"

    # YouTube Data API v3
    youtube_api_key: str

    # Reddit API (PRAW)
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "trend-setter/1.0"
    target_subreddits: Annotated[list[str], NoDecode] = ["popular", "trending"]

    # Google Trends (pytrends)
    google_trends_geo: str = "US"

    # Pipeline behavior
    trend_categories: Annotated[list[str], NoDecode] = [
        "entertainment",
        "technology",
        "lifestyle",
    ]
    post_interval_hours: int = 6
    max_trends_to_fetch: int = 10

    @field_validator("target_subreddits", "trend_categories", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        """Allow list fields to be set as a comma-separated env string."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
