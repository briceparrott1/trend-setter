"""Orchestrates one full trend-setter run.

Stages: trend discovery -> filter -> research -> brief -> video -> post.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from trend_setter.config import Settings
from trend_setter.generation.brief import generate_brief
from trend_setter.generation.video import generate_video
from trend_setter.posting.instagram import publish_reel
from trend_setter.research.perplexity import research_topic
from trend_setter.research.wikipedia import get_summary
from trend_setter.trends.aggregator import aggregate_trends
from trend_setter.trends.google_trends import fetch_rising_queries
from trend_setter.trends.youtube import fetch_trending_videos

logger = logging.getLogger(__name__)


async def run_pipeline(settings: Settings) -> str | None:
    """Run one full pipeline cycle: fetch trends, research, generate, and post a Reel.

    Stages:
        1. Fetch trending signals from Google Trends and YouTube in
           parallel, then merge them with NewsData.io headlines and run
           every candidate through the 4-gate topic filter.
        2. Research the top surviving candidate via Perplexity Sonar, with
           a free Wikipedia enrichment lookup alongside it.
        3. Use Gemini (Google AI Studio) to write a narrated-explainer
           brief (script, shot descriptions, caption, hashtags).
        4. Use Kling AI to generate a short video from the brief's shot
           descriptions.
        5. Publish the video as an Instagram Reel.

    Args:
        settings: Application settings controlling every stage.

    Returns:
        The published Instagram media ID, or None if no candidate topic
        survived the trend filter this cycle.
    """
    google_trends, youtube_trends = await asyncio.gather(
        asyncio.to_thread(
            fetch_rising_queries,
            settings.trend_categories,
            settings.google_trends_geo,
            settings.max_trends_to_fetch,
        ),
        asyncio.to_thread(
            fetch_trending_videos,
            settings.youtube_api_key,
            max_results=settings.max_trends_to_fetch,
        ),
    )

    candidates = await aggregate_trends(
        google_trends,
        youtube_trends,
        settings,
        max_trends=settings.max_trends_to_fetch,
    )
    if not candidates:
        logger.info("no trend candidates survived filtering this cycle; skipping")
        return None
    top_candidate = candidates[0]

    sonar_research, wiki_summary = await asyncio.gather(
        research_topic(top_candidate.title, settings),
        get_summary(top_candidate.title),
    )
    research = {**sonar_research, "wikipedia": wiki_summary}

    brief = await generate_brief(top_candidate.title, research, settings)

    video_bytes = await generate_video(brief["shot_descriptions"], settings)

    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = Path(tmp_dir) / "reel.mp4"
        video_path.write_bytes(video_bytes)

        media_id = await publish_reel(
            video_path,
            caption=brief["caption"],
            access_token=settings.instagram_access_token,
            account_id=settings.instagram_account_id,
        )

    logger.info(
        "published Instagram Reel media_id=%s for topic=%s",
        media_id,
        top_candidate.title,
    )
    return media_id
