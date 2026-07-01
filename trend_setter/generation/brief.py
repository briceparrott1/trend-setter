"""Script and brief generation via Gemini (Google AI Studio)."""

from __future__ import annotations

import google.generativeai as genai

from trend_setter.config import Settings


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
    # TODO: call genai.GenerativeModel(settings.gemini_model)
    # .generate_content(prompt)
    settings = settings or Settings()
    configure_gemini(settings)
    raise NotImplementedError
