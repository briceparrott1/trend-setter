"""Veo 2 (Vertex AI): generate a short video from a video brief.

Veo is not yet exposed via a dedicated `vertexai` SDK class, so generation
goes through the Vertex AI REST `predictLongRunning` endpoint directly:
https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-videos
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import google.auth
import google.auth.transport.requests
import httpx

from trend_setter.generation.brief import VideoBrief

VERTEX_AI_API_BASE = "https://{location}-aiplatform.googleapis.com/v1"


@dataclass(slots=True)
class GeneratedVideo:
    """A locally saved video file produced by Veo 2."""

    file_path: Path
    duration_seconds: float


def generate_video(
    brief: VideoBrief,
    project: str,
    location: str,
    model_name: str,
    output_dir: Path,
) -> GeneratedVideo:
    """Use Veo 2 to generate a short video from a brief's scene description.

    Args:
        brief: The video brief to render, produced by `generate_brief`.
        project: Google Cloud project ID for Vertex AI.
        location: Vertex AI region (e.g. "us-central1").
        model_name: Veo model name (e.g. "veo-002").
        output_dir: Directory to write the generated video file into.

    Returns:
        A `GeneratedVideo` pointing at the rendered file on disk.
    """
    # TODO: obtain credentials via google.auth.default(), POST the prompt to
    # {model}:predictLongRunning, poll :fetchPredictOperation until done,
    # then decode/download the base64 video bytes into output_dir.
    credentials, _ = google.auth.default()
    endpoint = (
        f"{VERTEX_AI_API_BASE.format(location=location)}/projects/{project}"
        f"/locations/{location}/publishers/google/models/{model_name}"
        ":predictLongRunning"
    )
    with httpx.Client(base_url=endpoint):
        raise NotImplementedError
