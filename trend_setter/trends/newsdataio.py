"""NewsData.io: discover trending topics linked to current news coverage."""

from __future__ import annotations

import httpx

from trend_setter.config import Settings

NEWSDATAIO_URL = "https://newsdata.io/api/1/latest"


async def fetch_trending_news(settings: Settings | None = None) -> list[dict]:
    """Fetch latest headlines from NewsData.io.

    Returns:
        List of dicts with 'title', 'source_id', 'link', 'pubDate', 'category'.
    """
    # TODO: GET NEWSDATAIO_URL with apikey=settings.newsdataio_api_key,
    # language=en, size=settings.max_trends_to_fetch. Response key is
    # 'results'. Return parsed results list.
    settings = settings or Settings()
    async with httpx.AsyncClient(base_url=NEWSDATAIO_URL):
        raise NotImplementedError
