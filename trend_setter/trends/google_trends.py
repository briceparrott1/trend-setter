"""Google Trends client (via `pytrends`): rising search queries."""

from __future__ import annotations

from dataclasses import dataclass

from pytrends.request import TrendReq


@dataclass(slots=True)
class GoogleTrend:
    """A single rising query from Google Trends."""

    query: str
    rising_percent: float


def fetch_rising_queries(
    seed_keywords: list[str],
    geo: str = "US",
    max_results: int = 10,
) -> list[GoogleTrend]:
    """Fetch rising related queries for a set of seed keywords.

    Args:
        seed_keywords: Topics/keywords to seed the trend lookup with.
        geo: Geography to restrict results to (e.g. "US").
        max_results: Maximum number of rising queries to return.

    Returns:
        A list of rising queries ranked by breakout/rising percentage.
    """
    # TODO: build a TrendReq payload with seed_keywords, call
    # related_queries(), and merge the "rising" dataframe across keywords,
    # sorting by rising percentage (pytrends reports "Breakout" as a spike).
    TrendReq(hl="en-US", tz=360)
    raise NotImplementedError
