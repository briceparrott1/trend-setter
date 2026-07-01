"""TikTok Research API client: trending videos and hashtags.

https://developers.tiktok.com/doc/research-api-specs-query-videos
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

TIKTOK_RESEARCH_API_BASE = "https://open.tiktokapis.com/v2/research"


@dataclass(slots=True)
class TikTokTrend:
    """A single trending signal from the TikTok Research API."""

    hashtag: str
    video_count: int
    view_count: int


async def fetch_trending_hashtags(
    client_key: str,
    client_secret: str,
    max_results: int = 10,
) -> list[TikTokTrend]:
    """Fetch currently rising hashtags/videos from the TikTok Research API.

    Args:
        client_key: TikTok for Developers app client key.
        client_secret: TikTok for Developers app client secret.
        max_results: Maximum number of trends to return.

    Returns:
        A list of trending hashtags ranked by rising engagement.
    """
    # TODO: authenticate via client credentials grant, then query the
    # Research API's video/hashtag query endpoints and rank by rising
    # engagement (view/share velocity) within the lookback window.
    async with httpx.AsyncClient(base_url=TIKTOK_RESEARCH_API_BASE):
        raise NotImplementedError
