"""Research via Perplexity Sonar API: topic -> cited prose + candidate hook facts."""

from __future__ import annotations

import httpx

from trend_setter.config import Settings

SONAR_URL = "https://api.perplexity.ai/chat/completions"
SONAR_MODEL = "sonar"


async def research_topic(topic: str, settings: Settings | None = None) -> dict:
    """Query Perplexity Sonar for one surprising explainable fact about a topic.

    Returns:
        dict with keys: 'hook_fact' (str), 'supporting_facts' (list[str]),
        'citations' (list[str URLs]), 'raw_answer' (str).
    """
    # TODO: POST to SONAR_URL with Authorization: Bearer PERPLEXITY_API_KEY.
    # Prompt: "Give me ONE surprising counterintuitive fact about {topic}
    # that is explainable in under 45 seconds to a lay audience. Then give
    # 2-3 supporting facts. Cite authoritative sources. Return as JSON."
    # Parse and return structured result.
    settings = settings or Settings()
    async with httpx.AsyncClient(base_url=SONAR_URL):
        raise NotImplementedError
