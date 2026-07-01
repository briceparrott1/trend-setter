"""Reddit client (via PRAW): hot posts from configurable subreddits.

https://praw.readthedocs.io/
"""

from __future__ import annotations

from dataclasses import dataclass

import praw


@dataclass(slots=True)
class RedditTrend:
    """A single trending signal from Reddit."""

    title: str
    subreddit: str
    score: int
    num_comments: int


def fetch_hot_posts(
    client_id: str,
    client_secret: str,
    user_agent: str,
    subreddits: list[str],
    max_results: int = 10,
) -> list[RedditTrend]:
    """Fetch hot posts from the configured subreddits as trending signals.

    Args:
        client_id: Reddit app client ID.
        client_secret: Reddit app client secret.
        user_agent: User agent string identifying this app to Reddit's API.
        subreddits: Subreddit names to pull hot posts from (e.g. "popular").
        max_results: Maximum number of trends to return.

    Returns:
        A list of trending Reddit posts ranked by score.
    """
    # TODO: authenticate via praw.Reddit(client_id=..., client_secret=...,
    # user_agent=...), iterate subreddit.hot() for each configured
    # subreddit, and rank the combined results by score before truncating
    # to max_results.
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    reddit.subreddit("+".join(subreddits))
    raise NotImplementedError
