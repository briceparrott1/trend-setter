"""Merge trend signals from Google Trends, YouTube, and NewsData.io, then filter."""

from __future__ import annotations

from trend_setter.config import Settings
from trend_setter.trends.filter import TopicCandidate, filter_topics
from trend_setter.trends.google_trends import GoogleTrend
from trend_setter.trends.newsdataio import fetch_trending_news
from trend_setter.trends.youtube import YouTubeTrend

# Keyword heuristic for "scandalous/polarizing/controversial" signal — same
# cheap, deterministic style as the gate-1 explainability heuristic in
# `trends/filter.py`. Not exhaustive; a candidate's score is just how many
# of these keywords appear in its title (case-insensitive substring match).
_CONTROVERSY_KEYWORDS = frozenset(
    {
        "scandal",
        "scandalous",
        "backlash",
        "slammed",
        "slams",
        "accused",
        "accusation",
        "accusations",
        "controversy",
        "controversial",
        "banned",
        "ban",
        "feud",
        "outrage",
        "outraged",
        "outrages",
        "exposed",
        "expose",
        "blasted",
        "fury",
        "furious",
        "boycott",
        "boycotted",
        "cover-up",
        "coverup",
        "lawsuit",
        "sues",
        "sued",
        "shocking",
        "explosive",
        "denies",
        "denied",
        "criticized",
        "criticised",
        "condemn",
        "condemned",
        "backfire",
        "backfired",
        "leaked",
        "scandal-hit",
        "under fire",
        "fired",
        "resigns",
        "resign",
        "apologizes",
        "apologises",
    }
)


def _controversy_score(candidate: TopicCandidate) -> int:
    """Cheap keyword count of scandal/controversy signal in a candidate's title.

    Higher score = more provocative/divisive-reading. Used purely to rank
    already-filtered candidates before truncating to `max_trends`; it does
    not gate anything.
    """
    title_lower = candidate.title.lower()
    return sum(1 for keyword in _CONTROVERSY_KEYWORDS if keyword in title_lower)


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

    Candidates that survive the filter are then ranked by
    `_controversy_score` (most scandalous/polarizing-reading title first,
    stable sort preserving source-priority order among ties) before being
    capped at `max_trends`, per captain's direction to prioritize
    provocative topics over bland ones.

    Returns:
        Topic candidates that passed every gate, ranked by controversy
        score, capped at `max_trends`.
    """
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

    # Dedupe by normalized title, keeping the first (highest-priority
    # source order) occurrence of each.
    seen: set[str] = set()
    unique_candidates = []
    for candidate in candidates:
        key = candidate.title.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)

    filtered = filter_topics(unique_candidates)
    ranked = sorted(filtered, key=_controversy_score, reverse=True)
    return ranked[:max_trends]
