"""Settings load correctly from environment variables."""

from trend_setter.config import Settings

REQUIRED_ENV = {
    "INSTAGRAM_ACCESS_TOKEN": "test-token",
    "INSTAGRAM_ACCOUNT_ID": "12345",
    "GEMINI_API_KEY": "test-gemini-key",
    "KLING_API_KEY": "test-kling-key",
    "PERPLEXITY_API_KEY": "test-perplexity-key",
    "YOUTUBE_API_KEY": "test-yt-key",
    "NEWSDATAIO_API_KEY": "test-newsdataio-key",
    "OPENAI_API_KEY": "test-openai-key",
}


def test_settings_load_from_env(monkeypatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.instagram_access_token == "test-token"
    assert settings.instagram_account_id == "12345"
    assert settings.gemini_api_key == "test-gemini-key"
    assert settings.kling_api_key == "test-kling-key"
    assert settings.perplexity_api_key == "test-perplexity-key"
    assert settings.youtube_api_key == "test-yt-key"
    assert settings.newsdataio_api_key == "test-newsdataio-key"
    assert settings.openai_api_key == "test-openai-key"


def test_settings_defaults(monkeypatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.gemini_model == "gemini-2.0-flash-001"
    assert settings.google_trends_geo == "US"
    assert settings.trend_categories == [
        "education",
        "science",
        "technology",
        "history",
    ]
    assert settings.post_interval_hours == 6
    assert settings.max_trends_to_fetch == 10
    assert settings.video_output_dir == "output"
    assert settings.kling_api_base == "https://api.klingai.com"
    assert settings.kling_clip_duration == 5
    assert settings.kling_clips_per_video == 6
