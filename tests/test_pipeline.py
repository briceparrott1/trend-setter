"""Mock-based smoke test of the trend -> brief -> video -> post pipeline."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trend_setter.config import Settings
from trend_setter.generation.brief import VideoBrief
from trend_setter.generation.video import GeneratedVideo
from trend_setter.pipeline import run_pipeline
from trend_setter.trends.aggregator import RankedTrend


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        instagram_access_token="token",
        instagram_account_id="acct",
        google_cloud_project="proj",
        youtube_api_key="yt-key",
        tiktok_client_key="tt-key",
        tiktok_client_secret="tt-secret",
    )


async def test_run_pipeline_wires_all_stages(settings: Settings) -> None:
    ranked_trend = RankedTrend(topic="cats in hats", sources=["tiktok"], score=1.0)
    brief = VideoBrief(
        trend_topic="cats in hats",
        scene_description="a cat wearing a hat",
        caption="Cats in hats are trending!",
        hashtags=["#cats", "#trending"],
    )
    video = GeneratedVideo(file_path=Path("/tmp/video.mp4"), duration_seconds=8.0)

    with (
        patch(
            "trend_setter.pipeline.fetch_trending_hashtags",
            new=AsyncMock(return_value=["tiktok-trend"]),
        ),
        patch(
            "trend_setter.pipeline.fetch_trending_videos",
            new=MagicMock(return_value=["youtube-trend"]),
        ),
        patch(
            "trend_setter.pipeline.fetch_rising_queries",
            new=MagicMock(return_value=["google-trend"]),
        ),
        patch(
            "trend_setter.pipeline.aggregate_trends",
            new=MagicMock(return_value=[ranked_trend]),
        ) as mock_aggregate,
        patch(
            "trend_setter.pipeline.generate_brief", new=MagicMock(return_value=brief)
        ) as mock_brief,
        patch(
            "trend_setter.pipeline.generate_video", new=MagicMock(return_value=video)
        ) as mock_video,
        patch(
            "trend_setter.pipeline.publish_reel",
            new=AsyncMock(return_value="media-123"),
        ) as mock_publish,
    ):
        media_id = await run_pipeline(settings)

    assert media_id == "media-123"
    mock_aggregate.assert_called_once()
    mock_brief.assert_called_once_with(
        ranked_trend,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
        model_name=settings.gemini_model,
    )
    mock_video.assert_called_once()
    mock_publish.assert_called_once()
    assert mock_publish.call_args.kwargs["caption"] == brief.caption
