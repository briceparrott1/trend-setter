"""APScheduler setup and job registration for the trend-setter pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from trend_setter.config import Settings
from trend_setter.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Build an `AsyncIOScheduler` that runs the pipeline on a fixed interval.

    Args:
        settings: Application settings, including `post_interval_hours`.

    Returns:
        A configured (but not yet started) `AsyncIOScheduler`.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_pipeline_job,
        trigger="interval",
        hours=settings.post_interval_hours,
        args=[settings],
        id="trend_setter_pipeline",
        next_run_time=datetime.now(),
    )
    return scheduler


async def _run_pipeline_job(settings: Settings) -> None:
    """Scheduler entrypoint: run one full pipeline cycle and log the outcome."""
    try:
        await run_pipeline(settings)
    except Exception:
        logger.exception("trend-setter pipeline run failed")


def start(settings: Settings) -> None:
    """Start the scheduler and block forever running the asyncio event loop.

    Args:
        settings: Application settings used to configure the scheduler.
    """
    scheduler = build_scheduler(settings)
    scheduler.start()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
