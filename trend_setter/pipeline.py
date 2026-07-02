"""Orchestrates one full trend-setter run.

Stages: trend discovery -> filter -> research -> brief -> video -> post.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from trend_setter.config import Settings
from trend_setter.generation.brief import generate_brief
from trend_setter.generation.video import generate_video
from trend_setter.posting.instagram import publish_reel
from trend_setter.report import RunReport
from trend_setter.research.perplexity import research_topic
from trend_setter.research.wikipedia import get_summary
from trend_setter.trends.aggregator import aggregate_trends
from trend_setter.trends.google_trends import fetch_rising_queries
from trend_setter.trends.youtube import fetch_trending_videos

logger = logging.getLogger(__name__)


def _clip_paths_for_video(video_path: Path) -> list[str]:
    """Best-effort lookup of the intermediate clip files for a generated video.

    Relies on the `generate_video` output layout (see AGENTS.md's "Output
    layout" note): a final video at `trend_setter_{timestamp}.mp4` has its
    clips in a sibling `clips_{timestamp}/` directory. Returns `[]` if the
    directory isn't there rather than raising, since this is purely
    informational for the report.
    """
    timestamp = video_path.stem.removeprefix("trend_setter_")
    clips_dir = video_path.parent / f"clips_{timestamp}"
    if not clips_dir.is_dir():
        return []
    return sorted(str(p) for p in clips_dir.glob("clip_*.mp4"))


async def run_pipeline(settings: Settings) -> dict | None:
    """Run one full pipeline cycle: fetch trends, research, generate, and post a Reel.

    Stages:
        1. Fetch trending signals from Google Trends and YouTube in
           parallel, then merge them with NewsData.io headlines and run
           every candidate through the 4-gate topic filter.
        2. Research the top surviving candidate via Perplexity Sonar, with
           a free Wikipedia enrichment lookup alongside it.
        3. Use Gemini (Google AI Studio) to write a narrated-explainer
           brief (script, shot descriptions, caption, hashtags).
        4. Use Kling AI + OpenAI TTS to generate a short narrated video
           from the brief's script and shot descriptions.
        5. Publish the video as an Instagram Reel.

    Once a topic survives the trend filter, a `RunReport` (see
    `trend_setter.report`) is written to
    `{settings.video_output_dir}/report_{timestamp}.json` and rewritten to
    disk after every stage, so a failure partway through (e.g. a Kling/TTS
    error, or the `posting/instagram.py` `NotImplementedError` stub) still
    leaves the already-generated topic/research/brief/video recoverable on
    disk.

    Args:
        settings: Application settings controlling every stage.

    Returns:
        A dict with the topic, script, caption, shot descriptions,
        citations, video path, and published media ID — or None if no
        candidate topic survived the trend filter this cycle.
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

    report = RunReport.start(Path(settings.video_output_dir))
    report.update(
        status="topic_chosen",
        topic=top_candidate.title,
        source=top_candidate.source,
        category=top_candidate.category,
    )

    try:
        sonar_research, wiki_summary = await asyncio.gather(
            research_topic(top_candidate.title, settings),
            get_summary(top_candidate.title),
        )
        research = {**sonar_research, "wikipedia": wiki_summary}
        report.update(
            status="research_complete",
            citations=research.get("citations"),
            has_wikipedia_summary=bool(wiki_summary),
        )

        brief = await generate_brief(top_candidate.title, research, settings)
        report.update(
            status="brief_generated",
            script=brief.get("script"),
            caption=brief.get("caption"),
            shot_descriptions=brief.get("shot_descriptions"),
        )

        video_path = await generate_video(
            shot_descriptions=brief["shot_descriptions"],
            script=brief["script"],
            output_dir=Path(settings.video_output_dir),
            settings=settings,
        )
        report.update(
            status="video_generated",
            video_path=str(video_path),
            clip_paths=_clip_paths_for_video(video_path),
        )

        media_id = await publish_reel(
            video_path,
            caption=brief["caption"],
            access_token=settings.instagram_access_token,
            account_id=settings.instagram_account_id,
        )
        report.update(status="published", media_id=media_id)
    except Exception as exc:
        report.record_failure(exc)
        raise

    logger.info(
        "published Instagram Reel media_id=%s for topic=%s",
        media_id,
        top_candidate.title,
    )
    return {
        "topic": top_candidate.title,
        "script": brief.get("script"),
        "caption": brief.get("caption"),
        "shot_descriptions": brief.get("shot_descriptions"),
        "citations": research.get("citations"),
        "video_path": str(video_path),
        "media_id": media_id,
    }
