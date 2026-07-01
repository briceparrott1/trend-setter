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
    settings = settings or Settings()
    params = {
        "apikey": settings.newsdataio_api_key,
        "language": "en",
        "size": min(settings.max_trends_to_fetch, 10),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(NEWSDATAIO_URL, params=params)
        response.raise_for_status()
        data = response.json()

    results = []
    for article in data.get("results", [])[: settings.max_trends_to_fetch]:
        categories = article.get("category")
        category = (
            categories[0] if isinstance(categories, list) and categories else None
        )
        results.append(
            {
                "title": article.get("title", ""),
                "source_id": article.get("source_id"),
                "link": article.get("link"),
                "pubDate": article.get("pubDate"),
                "category": category,
            }
        )
    return results
