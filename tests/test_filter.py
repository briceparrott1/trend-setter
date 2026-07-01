"""The topic hard-gate filter must reject reject-category candidates."""

from trend_setter.trends.filter import TopicCandidate, filter_topics


def test_filter_topics_keeps_candidates_without_reject_category() -> None:
    candidates = [
        TopicCandidate(title="why octopuses have three hearts", source="newsdataio")
    ]

    assert filter_topics(candidates) == candidates


def test_filter_topics_rejects_gossip_category() -> None:
    candidates = [
        TopicCandidate(
            title="celebrity breakup news", source="newsdataio", category="gossip"
        ),
        TopicCandidate(title="why octopuses have three hearts", source="newsdataio"),
    ]

    result = filter_topics(candidates)

    assert [c.title for c in result] == ["why octopuses have three hearts"]
