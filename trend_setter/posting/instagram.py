"""Instagram Graph API client: upload and publish a Reel."""

from __future__ import annotations

from pathlib import Path

import httpx

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


async def publish_reel(
    video_path: Path,
    caption: str,
    access_token: str,
    account_id: str,
) -> str:
    """Upload a video and publish it as an Instagram Reel.

    Args:
        video_path: Local path to the video file to publish.
        caption: Caption text (including hashtags) for the Reel.
        access_token: Long-lived Page/Instagram access token.
        account_id: Instagram Business Account ID to publish to.

    Returns:
        The published media ID.
    """
    # TODO: two-step publish flow against the Graph API:
    #   1. POST /{account_id}/media with video_url (or resumable upload)
    #      and media_type="REELS" to create a container, poll status_code
    #      until FINISHED.
    #   2. POST /{account_id}/media_publish with the creation_id to
    #      publish the container, returning the resulting media id.
    async with httpx.AsyncClient(base_url=GRAPH_API_BASE):
        raise NotImplementedError
