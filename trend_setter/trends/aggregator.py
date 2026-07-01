"""Merge trend signals from TikTok, YouTube, and Google Trends."""

from __future__ import annotations

from dataclasses import dataclass

from trend_setter.trends.google_trends import GoogleTrend
from trend_setter.trends.tiktok import TikTokTrend
from trend_setter.trends.youtube import YouTubeTrend


@dataclass(slots=True)
class RankedTrend:
    """A single cross-platform trend signal ranked by aggregate strength."""

    topic: str
    sources: list[str]
    score: float


def aggregate_trends(
    tiktok_trends: list[TikTokTrend],
    youtube_trends: list[YouTubeTrend],
    google_trends: list[GoogleTrend],
    max_trends: int = 10,
) -> list[RankedTrend]:
    """Merge and rank trend signals across all three sources.

    Topics that appear across multiple sources are boosted, since
    cross-platform overlap is a stronger rising-trend signal than any
    single source alone.

    Args:
        tiktok_trends: Trends fetched from the TikTok Research API.
        youtube_trends: Trends fetched from YouTube Data API v3.
        google_trends: Rising queries fetched from Google Trends.
        max_trends: Maximum number of ranked trends to return.

    Returns:
        A list of `RankedTrend` sorted by descending score, capped at
        `max_trends`.
    """
    # TODO: normalize topic names across sources (casing, punctuation),
    # merge duplicate topics into one RankedTrend with a combined score,
    # and sort descending by score before truncating to max_trends.
    raise NotImplementedError
