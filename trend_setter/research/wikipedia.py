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
    # TODO: GET {WIKI_API}/{topic_slug}, return parsed JSON or None on 404.
    async with httpx.AsyncClient(base_url=WIKI_API):
        raise NotImplementedError
