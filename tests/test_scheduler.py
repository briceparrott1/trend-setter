"""The scheduled job must not start paused, and must fire on startup."""

import asyncio
from unittest.mock import AsyncMock, patch

from trend_setter.config import Settings
from trend_setter.scheduler import build_scheduler


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        instagram_access_token="token",
        instagram_account_id="acct",
        google_cloud_project="proj",
        youtube_api_key="yt-key",
        tiktok_client_key="tt-key",
        tiktok_client_secret="tt-secret",
    )


def test_build_scheduler_job_is_not_paused() -> None:
    scheduler = build_scheduler(_settings())

    job = scheduler.get_job("trend_setter_pipeline")

    # `next_run_time=None` is how APScheduler represents a paused job, which
    # would mean the pipeline never runs until someone manually resumes it.
    assert job.next_run_time is not None


async def test_scheduler_runs_pipeline_shortly_after_start() -> None:
    with patch(
        "trend_setter.scheduler.run_pipeline", new=AsyncMock(return_value="media-1")
    ) as mock_run_pipeline:
        scheduler = build_scheduler(_settings())
        scheduler.start()
        try:
            await asyncio.wait_for(_wait_until_called(mock_run_pipeline), timeout=5.0)
        finally:
            scheduler.shutdown(wait=False)

    mock_run_pipeline.assert_called_once()


async def _wait_until_called(mock: AsyncMock) -> None:
    while not mock.called:
        await asyncio.sleep(0.05)
