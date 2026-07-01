"""Settings load correctly from environment variables."""

from trend_setter.config import Settings

REQUIRED_ENV = {
    "INSTAGRAM_ACCESS_TOKEN": "test-token",
    "INSTAGRAM_ACCOUNT_ID": "12345",
    "GOOGLE_CLOUD_PROJECT": "test-project",
    "YOUTUBE_API_KEY": "test-yt-key",
    "TIKTOK_CLIENT_KEY": "test-client-key",
    "TIKTOK_CLIENT_SECRET": "test-client-secret",
}


def test_settings_load_from_env(monkeypatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.instagram_access_token == "test-token"
    assert settings.instagram_account_id == "12345"
    assert settings.google_cloud_project == "test-project"
    assert settings.youtube_api_key == "test-yt-key"
    assert settings.tiktok_client_key == "test-client-key"
    assert settings.tiktok_client_secret == "test-client-secret"


def test_settings_defaults(monkeypatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.google_cloud_location == "us-central1"
    assert settings.gemini_model == "gemini-2.0-flash-001"
    assert settings.veo_model == "veo-002"
    assert settings.google_trends_geo == "US"
    assert settings.trend_categories == ["entertainment", "technology", "lifestyle"]
    assert settings.post_interval_hours == 6
    assert settings.max_trends_to_fetch == 10
