"""Orchestrates one full trend-setter run: trend -> brief -> video -> post."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from trend_setter.config import Settings
from trend_setter.generation.brief import generate_brief
from trend_setter.generation.video import generate_video
from trend_setter.posting.instagram import publish_reel
from trend_setter.trends.aggregator import aggregate_trends
from trend_setter.trends.google_trends import fetch_rising_queries
from trend_setter.trends.tiktok import fetch_trending_hashtags
from trend_setter.trends.youtube import fetch_trending_videos

logger = logging.getLogger(__name__)


async def run_pipeline(settings: Settings) -> str:
    """Run one full pipeline cycle: fetch trends, generate, and post a Reel.

    Stages:
        1. Fetch trending signals from TikTok, YouTube, and Google Trends
           in parallel.
        2. Aggregate the cross-platform signal into a ranked trend list and
           pick the top trend.
        3. Use Gemini to write a video brief + caption for that trend.
        4. Use Veo 2 to generate a short video from the brief.
        5. Publish the video as an Instagram Reel.

    Args:
        settings: Application settings controlling every stage.

    Returns:
        The published Instagram media ID.
    """
    tiktok_trends, youtube_trends, google_trends = await asyncio.gather(
        fetch_trending_hashtags(
            settings.tiktok_client_key,
            settings.tiktok_client_secret,
            max_results=settings.max_trends_to_fetch,
        ),
        asyncio.to_thread(
            fetch_trending_videos,
            settings.youtube_api_key,
            max_results=settings.max_trends_to_fetch,
        ),
        asyncio.to_thread(
            fetch_rising_queries,
            settings.trend_categories,
            settings.google_trends_geo,
            settings.max_trends_to_fetch,
        ),
    )

    ranked_trends = aggregate_trends(
        tiktok_trends,
        youtube_trends,
        google_trends,
        max_trends=settings.max_trends_to_fetch,
    )
    top_trend = ranked_trends[0]

    brief = generate_brief(
        top_trend,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
        model_name=settings.gemini_model,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        video = generate_video(
            brief,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            model_name=settings.veo_model,
            output_dir=Path(tmp_dir),
        )

        media_id = await publish_reel(
            video.file_path,
            caption=brief.caption,
            access_token=settings.instagram_access_token,
            account_id=settings.instagram_account_id,
        )

    logger.info(
        "published Instagram Reel media_id=%s for trend=%s", media_id, top_trend.topic
    )
    return media_id
