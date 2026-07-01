"""Unit tests for pytrends retry/backoff behavior in google_trends.py."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from trend_setter.trends.google_trends import GoogleTrend, fetch_rising_queries


def _fake_pytrends(rising_rows: list[dict]) -> MagicMock:
    pytrends = MagicMock()
    pytrends.related_queries.return_value = {
        "kw": {"rising": pd.DataFrame(rising_rows)}
    }
    return pytrends


def test_fetch_rising_queries_retries_three_times_then_returns_empty() -> None:
    failing_pytrends = MagicMock()
    failing_pytrends.related_queries.side_effect = requests.exceptions.ReadTimeout(
        "timed out"
    )

    with (
        patch(
            "trend_setter.trends.google_trends.TrendReq",
            return_value=failing_pytrends,
        ) as mock_trend_req,
        patch("trend_setter.trends.google_trends.time.sleep") as mock_sleep,
    ):
        result = fetch_rising_queries(["octopus"], geo="US", max_results=10)

    assert result == []
    assert mock_trend_req.call_count == 3
    assert failing_pytrends.related_queries.call_count == 3
    assert mock_sleep.call_args_list == [((2,),), ((4,),)]


def test_fetch_rising_queries_succeeds_after_one_retry() -> None:
    good_pytrends = _fake_pytrends([{"query": "octopus hearts", "value": "Breakout"}])
    attempts = {"n": 0}

    def _trend_req_factory(*args, **kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            failing = MagicMock()
            failing.related_queries.side_effect = requests.exceptions.ConnectionError(
                "connection reset"
            )
            return failing
        return good_pytrends

    with (
        patch(
            "trend_setter.trends.google_trends.TrendReq",
            side_effect=_trend_req_factory,
        ),
        patch("trend_setter.trends.google_trends.time.sleep") as mock_sleep,
    ):
        result = fetch_rising_queries(["octopus"], geo="US", max_results=10)

    assert result == [GoogleTrend(query="octopus hearts", rising_percent=float("inf"))]
    mock_sleep.assert_called_once_with(2)


def test_fetch_rising_queries_does_not_retry_on_other_errors() -> None:
    broken_pytrends = MagicMock()
    broken_pytrends.related_queries.side_effect = ValueError("unexpected")

    with (
        patch(
            "trend_setter.trends.google_trends.TrendReq",
            return_value=broken_pytrends,
        ),
        patch("trend_setter.trends.google_trends.time.sleep") as mock_sleep,
    ):
        with pytest.raises(ValueError, match="unexpected"):
            fetch_rising_queries(["octopus"], geo="US", max_results=10)

    mock_sleep.assert_not_called()
