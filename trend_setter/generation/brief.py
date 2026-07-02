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
Full research notes (read this carefully — it is the ONLY basis you may \
use to decide whether a specific claim is attributable to a named person):
{research_notes}
Sources: {citations}

Write a script with this exact structure:
- HOOK (0-3s): Open with the single strongest claim. Must land in the \
first 1.5 seconds. Choose exactly ONE of these two hook styles, based \
strictly on what the research notes above actually support:
    1. ATTRIBUTED hook — use this ONLY if the research notes contain a \
    specific, sourced claim or quote clearly attributable to one named \
    person (a named scientist, official, researcher, or other identified \
    individual who is on record with that specific claim). Phrase it as: \
    "Did you know [named person] believes/claims [Y]?" The CORE beat that \
    immediately follows must then contextualize it with "According to \
    [named person], ..." plus the actual sourced claim.
    2. NON-ATTRIBUTED hook — use this in every other case, including when \
    you are unsure: general facts, statistics, or findings with no single \
    clearly-named, directly-quotable person behind them. Never invent or \
    imply a specific person's belief, claim, or quote that the research \
    notes don't clearly support — that is a fabrication risk, not a style \
    choice. Instead phrase the hook as a general claim, e.g. "Some \
    believe...", "There's a claim that...", "Reportedly, ...", or a plain \
    surprising-fact framing ("Did you know [surprising fact]?").
    When in doubt, default to the NON-ATTRIBUTED hook.
- CORE (4-20s): Expand on the hook with 1 central idea. If you used the \
ATTRIBUTED hook, this is where the "According to [named person]..." \
contextualization goes. Clear, simple language.
- DETAILS (20-35s): Add 2-3 supporting facts that build on the core idea.
- SOURCE_CTA (35-45s): Cite the source(s) by name and say "follow for more \
facts like this."

Target: 60-85 words total. Simple vocabulary. No jargon.

Also write:
- 6 shot descriptions for AI video generation (one sentence each, \
cinematic style). Each shot MUST feature real people actively DOING \
something concrete and relevant to the topic — demonstrating, reacting, \
gesturing, in motion — not a static establishing shot of an empty scene \
or a slow camera pan. No on-screen text in any shot.
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

    # Passed through so the model has enough raw context to judge whether a
    # claim is genuinely attributable to a named person (see the ATTRIBUTED
    # vs. NON-ATTRIBUTED hook branches in SCRIPT_PROMPT) — the extracted
    # hook_fact/supporting_facts fields alone are usually too condensed to
    # carry that judgment.
    research_notes_parts = []
    raw_answer = research.get("raw_answer", "")
    if raw_answer:
        research_notes_parts.append(raw_answer)
    wikipedia = research.get("wikipedia")
    if isinstance(wikipedia, dict) and wikipedia.get("extract"):
        research_notes_parts.append(wikipedia["extract"])
    research_notes = "\n".join(research_notes_parts) or "No additional research notes."

    prompt = SCRIPT_PROMPT.format(
        topic=topic,
        hook_fact=research.get("hook_fact", ""),
        supporting_facts=supporting_facts,
        research_notes=research_notes,
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
