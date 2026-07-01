"""NewsAPI: discover trending topics linked to current news coverage."""

from __future__ import annotations

import httpx

from trend_setter.config import Settings

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"


async def fetch_trending_news(settings: Settings | None = None) -> list[dict]:
    """Fetch top headlines from NewsAPI.

    Returns:
        List of dicts with 'title', 'source', 'url', 'publishedAt'.
    """
    # TODO: GET NEWSAPI_URL with apiKey=settings.newsapi_key, country=us,
    # pageSize=settings.max_trends_to_fetch. Return parsed articles list.
    settings = settings or Settings()
    async with httpx.AsyncClient(base_url=NEWSAPI_URL):
        raise NotImplementedError
