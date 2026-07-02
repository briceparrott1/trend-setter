"""Hard-gate topic filter: a topic must pass every remaining gate to proceed."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MIN_WORDS = 4
_TITLE_CASE_WORD = re.compile(r"^[A-Z][\w'-]*$")


@dataclass
class TopicCandidate:
    """A candidate topic pulled from one of the trend sources."""

    title: str
    source: str  # 'google_trends' | 'youtube' | 'newsdataio'
    category: str | None = None
    raw: dict | None = None


def passes_gate_1_explainability(topic: TopicCandidate) -> bool:
    """Gate 1: topic must be explainable in <45s to a lay audience.

    Heuristic: reject titles under 4 words as too vague to build a script
    from, and reject titles that read as a bare proper name with no
    context — every word capitalized and no digits, e.g. "Taylor Swift
    Eras Tour" — since those have no explanatory angle to hang a script
    on. A real explainer topic ("why octopuses have three hearts") mixes
    in lowercase connector/verb words even in Title Case headlines.

    TODO: supplement with a lightweight LLM check via Gemini for ambiguous
    cases.
    """
    words = topic.title.split()
    if len(words) < _MIN_WORDS:
        return False

    has_number = any(char.isdigit() for char in topic.title)
    all_title_case = all(_TITLE_CASE_WORD.match(word) for word in words)
    if all_title_case and not has_number:
        return False

    return True


def passes_gate_2_surprising_angle(topic: TopicCandidate) -> bool:
    """Gate 2: topic must have a verifiable counterintuitive angle.

    This gate is intentionally a pass-through stub here: whether a topic
    has a surprising angle can't be known until Perplexity Sonar has
    actually researched it, which only happens in `pipeline.run_pipeline`
    after this pre-research filter has already run. There is nothing to
    check yet at this point in the pipeline.
    """
    return True


def passes_gate_3_authoritative_sources(topic: TopicCandidate) -> bool:
    """Gate 3: topic must have >=2 authoritative sources (Wikipedia or major outlet).

    Like gate 2, this is intentionally a pass-through stub: source/citation
    count is only known once the research call (Sonar citations, Wikipedia
    lookup) has run in `pipeline.run_pipeline`. There is nothing to check
    yet at this point in the pipeline.
    """
    return True


def filter_topics(candidates: list[TopicCandidate]) -> list[TopicCandidate]:
    """Apply every gate. Returns only candidates that pass all of them.

    There is no gossip/celebrity/sports rejection gate — scandalous,
    polarizing, and celebrity-adjacent topics are intentionally allowed
    through (and ranked ahead of bland ones by
    `trends.aggregator.aggregate_trends`), per captain's direction to
    prioritize engaging/provocative content over "safe" topics.
    """
    if not candidates:
        return []

    gates = [
        passes_gate_1_explainability,
        passes_gate_3_authoritative_sources,
        passes_gate_2_surprising_angle,  # post-research
    ]
    return [c for c in candidates if all(g(c) for g in gates)]
