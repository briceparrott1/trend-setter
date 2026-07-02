"""The topic hard-gate filter no longer rejects gossip/celebrity candidates."""

from trend_setter.trends.filter import TopicCandidate, filter_topics


def test_filter_topics_keeps_candidates_without_reject_category() -> None:
    candidates = [
        TopicCandidate(title="why octopuses have three hearts", source="newsdataio")
    ]

    assert filter_topics(candidates) == candidates


def test_filter_topics_keeps_gossip_category_candidates() -> None:
    """Gate 4 (gossip/celebrity rejection) was removed by captain's direction —
    scandalous/celebrity topics should now pass through the filter."""
    candidates = [
        TopicCandidate(
            title="celebrity affair scandal rocks hollywood",
            source="newsdataio",
            category="gossip",
        ),
        TopicCandidate(title="why octopuses have three hearts", source="newsdataio"),
    ]

    result = filter_topics(candidates)

    assert [c.title for c in result] == [c.title for c in candidates]
