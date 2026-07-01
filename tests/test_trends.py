"""Unit tests for the topic filter gates and aggregator dedup logic."""

from unittest.mock import AsyncMock, patch

from trend_setter.config import Settings
from trend_setter.trends.aggregator import aggregate_trends
from trend_setter.trends.filter import (
    TopicCandidate,
    passes_gate_1_explainability,
    passes_gate_4_not_gossip,
)
from trend_setter.trends.google_trends import GoogleTrend
from trend_setter.trends.youtube import YouTubeTrend


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        instagram_access_token="token",
        instagram_account_id="acct",
        gemini_api_key="gemini-key",
        kling_api_key="kling-key",
        perplexity_api_key="perplexity-key",
        youtube_api_key="yt-key",
        newsdataio_api_key="newsdataio-key",
        openai_api_key="openai-key",
    )


# -- Gate 1: explainability -------------------------------------------------


def test_gate_1_rejects_titles_under_four_words() -> None:
    topic = TopicCandidate(title="celebrity breakup news", source="newsdataio")

    assert passes_gate_1_explainability(topic) is False


def test_gate_1_rejects_bare_proper_name_with_no_context() -> None:
    topic = TopicCandidate(title="Taylor Swift Eras Tour", source="youtube")

    assert passes_gate_1_explainability(topic) is False


def test_gate_1_accepts_lowercase_explainer_phrase() -> None:
    topic = TopicCandidate(title="why octopuses have three hearts", source="newsdataio")

    assert passes_gate_1_explainability(topic) is True


def test_gate_1_accepts_title_case_headline_with_a_number() -> None:
    topic = TopicCandidate(
        title="Scientists Discover 3 New Species Today", source="newsdataio"
    )

    assert passes_gate_1_explainability(topic) is True


# -- Gate 4: not gossip/celebrity/sports/gaming/music -----------------------


def test_gate_4_rejects_youtube_entertainment_category_id() -> None:
    topic = TopicCandidate(title="some video", source="youtube", category="24")

    assert passes_gate_4_not_gossip(topic) is False


def test_gate_4_rejects_youtube_gaming_category_id() -> None:
    topic = TopicCandidate(title="some video", source="youtube", category="20")

    assert passes_gate_4_not_gossip(topic) is False


def test_gate_4_accepts_youtube_science_category_id() -> None:
    topic = TopicCandidate(title="some video", source="youtube", category="28")

    assert passes_gate_4_not_gossip(topic) is True


def test_gate_4_accepts_missing_category() -> None:
    topic = TopicCandidate(title="some article", source="newsdataio")

    assert passes_gate_4_not_gossip(topic) is True


# -- Aggregator dedup --------------------------------------------------------


async def test_aggregate_trends_dedupes_case_and_whitespace_across_sources() -> None:
    google_trends = [
        GoogleTrend(query="why octopuses have three hearts", rising_percent=100.0)
    ]
    youtube_trends = [
        YouTubeTrend(
            title="  Why Octopuses Have Three Hearts  ",
            video_id="abc123",
            category_id="27",
            view_count=1000,
        )
    ]
    news_articles = [{"title": "WHY OCTOPUSES HAVE THREE HEARTS"}]

    with patch(
        "trend_setter.trends.aggregator.fetch_trending_news",
        new=AsyncMock(return_value=news_articles),
    ):
        candidates = await aggregate_trends(
            google_trends, youtube_trends, _settings(), max_trends=10
        )

    # All three sources report the same topic (modulo case/whitespace); only
    # the first occurrence (Google Trends) should survive deduplication.
    assert len(candidates) == 1
    assert candidates[0].source == "google_trends"
