"""Google Trends client (via `pytrends`): rising search queries."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


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

    Retries up to 3 times with exponential backoff (2s, 4s, 8s) on pytrends
    read timeouts / connection errors. If all attempts fail, logs an error
    and returns an empty list rather than raising — `aggregate_trends`
    already handles an empty Google Trends source gracefully.

    Args:
        seed_keywords: Topics/keywords to seed the trend lookup with.
        geo: Geography to restrict results to (e.g. "US").
        max_results: Maximum number of rising queries to return.

    Returns:
        A list of rising queries ranked by breakout/rising percentage.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return _fetch_rising_queries_once(seed_keywords, geo, max_results)
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ) as e:
            if attempt == MAX_ATTEMPTS:
                logger.error("pytrends failed after %d attempts: %s", MAX_ATTEMPTS, e)
                return []
            wait = 2**attempt
            logger.warning(
                "pytrends attempt %d failed: %s, retrying in %ds...", attempt, e, wait
            )
            time.sleep(wait)
    return []


def _fetch_rising_queries_once(
    seed_keywords: list[str], geo: str, max_results: int
) -> list[GoogleTrend]:
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
