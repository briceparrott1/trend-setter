"""Research via Perplexity Sonar API: topic -> cited prose + candidate hook facts."""

from __future__ import annotations

import json

import httpx

from trend_setter.config import Settings

SONAR_URL = "https://api.perplexity.ai/chat/completions"
SONAR_MODEL = "sonar"

RESEARCH_PROMPT = """Give me ONE surprising, counterintuitive fact about \
"{topic}" that is explainable in under 45 seconds to a lay audience and \
genuinely non-obvious (not common knowledge). Then give 2-3 supporting \
facts that add context. Cite authoritative sources.

Respond with valid JSON only, no markdown, in this exact shape:
{{
  "hook_fact": "the single most surprising fact, 1-2 sentences",
  "supporting_facts": ["fact 1", "fact 2", "fact 3"]
}}"""


async def research_topic(topic: str, settings: Settings | None = None) -> dict:
    """Query Perplexity Sonar for one surprising explainable fact about a topic.

    Returns:
        dict with keys: 'hook_fact' (str), 'supporting_facts' (list[str]),
        'citations' (list[str URLs]), 'raw_answer' (str).
    """
    settings = settings or Settings()
    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": SONAR_MODEL,
        "messages": [{"role": "user", "content": RESEARCH_PROMPT.format(topic=topic)}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(SONAR_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_answer = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])

    content = raw_answer.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    parsed = json.loads(content.strip())

    return {
        "hook_fact": parsed.get("hook_fact", ""),
        "supporting_facts": parsed.get("supporting_facts", []),
        "citations": citations,
        "raw_answer": raw_answer,
    }
