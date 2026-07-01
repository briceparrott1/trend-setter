"""YouTube Data API v3 client: trending videos and rising search terms."""

from __future__ import annotations

from dataclasses import dataclass

from googleapiclient.discovery import build


@dataclass(slots=True)
class YouTubeTrend:
    """A single trending signal from YouTube."""

    title: str
    video_id: str
    category_id: str
    view_count: int


def fetch_trending_videos(
    api_key: str,
    region_code: str = "US",
    max_results: int = 10,
) -> list[YouTubeTrend]:
    """Fetch the current `mostPopular` chart from YouTube Data API v3.

    Args:
        api_key: YouTube Data API v3 key.
        region_code: ISO 3166-1 alpha-2 region code to fetch trends for.
        max_results: Maximum number of trends to return.

    Returns:
        A list of currently trending YouTube videos.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    response = (
        youtube.videos()
        .list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region_code,
            maxResults=max_results,
        )
        .execute()
    )
    trends = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        trends.append(
            YouTubeTrend(
                title=snippet.get("title", ""),
                video_id=item.get("id", ""),
                category_id=snippet.get("categoryId", ""),
                view_count=int(statistics.get("viewCount", 0)),
            )
        )
    return trends


def fetch_rising_search_terms(
    api_key: str,
    query: str,
    max_results: int = 10,
) -> list[str]:
    """Fetch rising search terms related to a seed query via YouTube search.

    Args:
        api_key: YouTube Data API v3 key.
        query: Seed query/topic to expand into related rising terms.
        max_results: Maximum number of terms to return.

    Returns:
        A list of related search terms.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    response = (
        youtube.search()
        .list(
            part="snippet",
            q=query,
            type="video",
            order="viewCount",
            maxResults=max_results,
        )
        .execute()
    )
    return [
        item["snippet"]["title"]
        for item in response.get("items", [])
        if item.get("snippet", {}).get("title")
    ]
