"""Video generation via Kling AI."""

from __future__ import annotations

import httpx

from trend_setter.config import Settings

KLING_API_BASE = "https://api.klingai.com"


async def generate_clip(
    brief: str,
    duration_seconds: int = 5,
    settings: Settings | None = None,
) -> bytes:
    """Generate a single video clip via Kling AI.

    Args:
        brief: Cinematic single-sentence shot description (what the camera
            sees).
        duration_seconds: Clip length; Kling standard supports 5 or 10s.
        settings: App settings; loaded from env if not provided.

    Returns:
        Raw video bytes (mp4).
    """
    # TODO: POST to KLING_API_BASE/v1/videos/text2video with bearer auth,
    # poll the task status endpoint until complete, download and return
    # mp4 bytes.
    settings = settings or Settings()
    async with httpx.AsyncClient(base_url=KLING_API_BASE):
        raise NotImplementedError


async def generate_video(clips: list[str], settings: Settings | None = None) -> bytes:
    """Generate a full narrated-explainer video from a list of shot descriptions.

    Generates each clip independently and concatenates them in order.
    Target: 6 clips x 5s = 30s total.
    """
    # TODO: gather([generate_clip(c) for c in clips]), ffmpeg-concat,
    # return mp4 bytes.
    settings = settings or Settings()
    raise NotImplementedError
