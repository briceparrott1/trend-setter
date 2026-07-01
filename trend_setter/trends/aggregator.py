"""Merge trend signals from Google Trends, YouTube, and NewsData.io, then filter."""

from __future__ import annotations

from trend_setter.config import Settings
from trend_setter.trends.filter import TopicCandidate, filter_topics
from trend_setter.trends.google_trends import GoogleTrend
from trend_setter.trends.newsdataio import fetch_trending_news
from trend_setter.trends.youtube import YouTubeTrend


async def aggregate_trends(
    google_trends: list[GoogleTrend],
    youtube_trends: list[YouTubeTrend],
    settings: Settings,
    max_trends: int = 10,
) -> list[TopicCandidate]:
    """Merge trend signals across sources and apply the topic hard-gate filter.

    Fetches NewsData.io headlines directly and combines them with the
    already-fetched Google Trends and YouTube signals before running every
    candidate through the 4-gate filter in `trends/filter.py`.

    Args:
        google_trends: Rising queries fetched from Google Trends.
        youtube_trends: Trends fetched from YouTube Data API v3.
        settings: App settings, used to fetch NewsData.io headlines.
        max_trends: Maximum number of candidates to return after filtering.

    Returns:
        Topic candidates that passed all 4 gates, capped at `max_trends`.
    """
    # TODO: normalize/dedupe topic titles across sources before filtering,
    # and rank surviving candidates by cross-platform overlap.
    news_articles = await fetch_trending_news(settings)
    candidates = [
        *(TopicCandidate(title=t.query, source="google_trends") for t in google_trends),
        *(
            TopicCandidate(title=t.title, source="youtube", category=t.category_id)
            for t in youtube_trends
        ),
        *(
            TopicCandidate(title=a["title"], source="newsdataio", raw=a)
            for a in news_articles
        ),
    ]
    return filter_topics(candidates)[:max_trends]
