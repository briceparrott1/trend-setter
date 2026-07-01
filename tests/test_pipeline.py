"""Mock-based smoke test of the trend -> research -> brief -> video -> post pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trend_setter.config import Settings
from trend_setter.pipeline import run_pipeline
from trend_setter.trends.filter import TopicCandidate


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        instagram_access_token="token",
        instagram_account_id="acct",
        gemini_api_key="gemini-key",
        kling_api_key="kling-key",
        perplexity_api_key="perplexity-key",
        youtube_api_key="yt-key",
        newsdataio_api_key="newsdataio-key",
    )


async def test_run_pipeline_wires_all_stages(settings: Settings) -> None:
    top_candidate = TopicCandidate(
        title="why octopuses have three hearts", source="newsdataio"
    )
    research = {
        "hook_fact": "Octopuses have three hearts.",
        "supporting_facts": ["Two pump blood to the gills."],
        "citations": ["https://example.com"],
        "raw_answer": "...",
    }
    wiki_summary = {"extract": "An octopus is...", "content_urls": {}}
    brief = {
        "script": "Did you know...",
        "shot_descriptions": [f"shot {i}" for i in range(6)],
        "caption": "Three hearts, one wild fact!",
        "hashtags": ["#octopus", "#science"],
    }
    video_bytes = b"fake-mp4-bytes"

    with (
        patch(
            "trend_setter.pipeline.fetch_rising_queries",
            new=MagicMock(return_value=["google-trend"]),
        ),
        patch(
            "trend_setter.pipeline.fetch_trending_videos",
            new=MagicMock(return_value=["youtube-trend"]),
        ),
        patch(
            "trend_setter.pipeline.aggregate_trends",
            new=AsyncMock(return_value=[top_candidate]),
        ) as mock_aggregate,
        patch(
            "trend_setter.pipeline.research_topic",
            new=AsyncMock(return_value=research),
        ) as mock_research,
        patch(
            "trend_setter.pipeline.get_summary",
            new=AsyncMock(return_value=wiki_summary),
        ) as mock_wiki,
        patch(
            "trend_setter.pipeline.generate_brief", new=AsyncMock(return_value=brief)
        ) as mock_brief,
        patch(
            "trend_setter.pipeline.generate_video",
            new=AsyncMock(return_value=video_bytes),
        ) as mock_video,
        patch(
            "trend_setter.pipeline.publish_reel",
            new=AsyncMock(return_value="media-123"),
        ) as mock_publish,
    ):
        media_id = await run_pipeline(settings)

    assert media_id == "media-123"
    mock_aggregate.assert_called_once()
    mock_research.assert_called_once_with(top_candidate.title, settings)
    mock_wiki.assert_called_once_with(top_candidate.title)
    mock_brief.assert_called_once_with(
        top_candidate.title,
        {**research, "wikipedia": wiki_summary},
        settings,
    )
    mock_video.assert_called_once_with(brief["shot_descriptions"], settings)
    mock_publish.assert_called_once()
    assert mock_publish.call_args.kwargs["caption"] == brief["caption"]


async def test_run_pipeline_returns_none_when_no_candidates(
    settings: Settings,
) -> None:
    with (
        patch(
            "trend_setter.pipeline.fetch_rising_queries",
            new=MagicMock(return_value=["google-trend"]),
        ),
        patch(
            "trend_setter.pipeline.fetch_trending_videos",
            new=MagicMock(return_value=["youtube-trend"]),
        ),
        patch(
            "trend_setter.pipeline.aggregate_trends",
            new=AsyncMock(return_value=[]),
        ),
        patch("trend_setter.pipeline.research_topic", new=AsyncMock()) as mock_research,
        patch("trend_setter.pipeline.get_summary", new=AsyncMock()) as mock_wiki,
    ):
        media_id = await run_pipeline(settings)

    assert media_id is None
    mock_research.assert_not_called()
    mock_wiki.assert_not_called()
