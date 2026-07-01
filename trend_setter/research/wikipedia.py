"""Wikipedia REST API: free enrichment and fact-checking layer."""

from __future__ import annotations

import httpx

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary"


async def get_summary(topic: str) -> dict | None:
    """Fetch the Wikipedia summary for a topic.

    Returns:
        dict with 'extract' (str) and 'content_urls' (dict), or None if not
        found.
    """
    slug = topic.strip().replace(" ", "_")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{WIKI_API}/{slug}",
                headers={"User-Agent": "trend-setter/1.0 (educational bot)"},
            )
        except httpx.HTTPError:
            return None

        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

    return {
        "extract": data.get("extract", ""),
        "content_urls": data.get("content_urls", {}),
    }
