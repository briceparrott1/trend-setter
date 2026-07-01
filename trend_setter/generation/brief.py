"""Script and brief generation via Gemini (Google AI Studio)."""

from __future__ import annotations

import asyncio
import json

import google.generativeai as genai

from trend_setter.config import Settings

SCRIPT_PROMPT = """You are writing a script for a 30-45 second educational \
Instagram Reel in narrated explainer format.

Topic: {topic}
Hook fact: {hook_fact}
Supporting facts:
{supporting_facts}
Sources: {citations}

Write a script with this exact structure:
- HOOK (0-3s): Start with the surprising fact as a bold claim or question. \
Must land in the first 1.5 seconds.
- CORE (4-20s): Expand on the hook with 1 central idea. Clear, simple \
language.
- DETAILS (20-35s): Add 2-3 supporting facts that build on the core idea.
- SOURCE_CTA (35-45s): Cite the source(s) by name and say "follow for more \
facts like this."

Target: 60-85 words total. Simple vocabulary. No jargon.

Also write:
- 6 shot descriptions for AI video generation (one sentence each \
describing what the camera sees, cinematic style, no text/people)
- An Instagram caption (2-3 sentences + hashtags)

Respond with valid JSON only, no markdown, in this exact shape:
{{
  "script": "the complete hook+core+details+source_cta script as one block",
  "shot_descriptions": ["shot 1", "shot 2", "shot 3", "shot 4", "shot 5", "shot 6"],
  "caption": "Instagram caption with hashtags",
  "hashtags": ["#hashtag1", "#hashtag2"]
}}"""


def configure_gemini(settings: Settings) -> None:
    """Configure the Gemini SDK with the API key."""
    genai.configure(api_key=settings.gemini_api_key)


async def generate_brief(
    topic: str, research: dict, settings: Settings | None = None
) -> dict:
    """Generate a narrated-explainer brief from a researched topic.

    Narrated explainer structure:
    - Hook (0-3s): surprising stat or bold claim from research['hook_fact']
    - Core fact (4-20s): expand the hook with 1 central idea
    - Supporting details (20-35s): 2-3 facts from research['supporting_facts']
    - Source/CTA (last 5-10s): cite sources, call to follow

    Returns:
        dict with 'script' (str, 60-85 words), 'shot_descriptions'
        (list[str], 6 items), 'caption' (str), 'hashtags' (list[str]).
    """
    settings = settings or Settings()
    configure_gemini(settings)
    model = genai.GenerativeModel(settings.gemini_model)

    supporting_facts = "\n".join(
        f"- {fact}" for fact in research.get("supporting_facts", [])
    )
    citations = ", ".join(research.get("citations", [])[:3]) or "authoritative sources"

    prompt = SCRIPT_PROMPT.format(
        topic=topic,
        hook_fact=research.get("hook_fact", ""),
        supporting_facts=supporting_facts,
        citations=citations,
    )

    def _generate() -> str:
        response = model.generate_content(prompt)
        return response.text

    content = await asyncio.to_thread(_generate)

    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    return json.loads(content)
