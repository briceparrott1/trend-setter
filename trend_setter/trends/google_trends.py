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
    pytrends = TrendReq(hl="en-US", tz=360)
    trends: list[GoogleTrend] = []

    # pytrends only accepts up to 5 keywords per payload.
    for i in range(0, len(seed_keywords), 5):
        batch = seed_keywords[i : i + 5]
        pytrends.build_payload(batch, geo=geo)
        related = pytrends.related_queries()
        for keyword_results in related.values():
            rising_df = keyword_results.get("rising")
            if rising_df is None or rising_df.empty:
                continue
            for _, row in rising_df.iterrows():
                value = row["value"]
                # pytrends reports a spike as the literal string "Breakout"
                # instead of a percentage; treat it as the highest rank.
                rising_percent = float("inf") if value == "Breakout" else float(value)
                trends.append(
                    GoogleTrend(query=row["query"], rising_percent=rising_percent)
                )

    trends.sort(key=lambda t: t.rising_percent, reverse=True)
    return trends[:max_results]
