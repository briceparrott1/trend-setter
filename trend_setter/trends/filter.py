"""Hard-gate topic filter: a topic must pass ALL 4 gates to proceed to research."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TopicCandidate:
    """A candidate topic pulled from one of the trend sources."""

    title: str
    source: str  # 'google_trends' | 'youtube' | 'newsapi'
    category: str | None = None
    raw: dict | None = None


REJECT_CATEGORIES = frozenset(
    {
        "celebrity",
        "gossip",
        "sports",
        "entertainment",
        "gaming",
        "music-charts",
        "reality-tv",
    }
)


def passes_gate_1_explainability(topic: TopicCandidate) -> bool:
    """Gate 1: topic must be explainable in <45s to a lay audience.

    Heuristic: reject topics whose title is a proper name with no context
    (pure celebrity/athlete names), or topics flagged in a reject-category
    source.

    TODO: supplement with a lightweight LLM check via Gemini for ambiguous
    cases.
    """
    # TODO: implement heuristic checks
    return True


def passes_gate_2_surprising_angle(topic: TopicCandidate) -> bool:
    """Gate 2: topic must have a verifiable counterintuitive angle.

    TODO: checked at research time via Perplexity Sonar — this gate is a
    post-research check, not a pre-research filter. Mark as pending.
    """
    return True


def passes_gate_3_authoritative_sources(topic: TopicCandidate) -> bool:
    """Gate 3: topic must have >=2 authoritative sources (Wikipedia or major outlet).

    TODO: quick Wikipedia lookup to confirm article exists; Sonar citation
    count check after research call.
    """
    return True


def passes_gate_4_not_gossip(topic: TopicCandidate) -> bool:
    """Gate 4: topic must not be pure celebrity/sports/gossip.

    Uses category metadata from the source feed where available.
    """
    if topic.category and topic.category.lower() in REJECT_CATEGORIES:
        return False
    # TODO: LLM-based content classification for topics with no category
    # metadata.
    return True


def filter_topics(candidates: list[TopicCandidate]) -> list[TopicCandidate]:
    """Apply all 4 gates. Returns only candidates that pass every gate."""
    gates = [
        passes_gate_1_explainability,
        passes_gate_4_not_gossip,  # cheap — run before API calls
        passes_gate_3_authoritative_sources,
        passes_gate_2_surprising_angle,  # post-research
    ]
    return [c for c in candidates if all(g(c) for g in gates)]
