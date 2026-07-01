"""Gemini (Vertex AI): turn a ranked trend signal into a video brief + caption."""

from __future__ import annotations

from dataclasses import dataclass

import vertexai
from vertexai.generative_models import GenerativeModel

from trend_setter.trends.aggregator import RankedTrend


@dataclass(slots=True)
class VideoBrief:
    """A generated brief describing the video to produce, plus its caption."""

    trend_topic: str
    scene_description: str
    caption: str
    hashtags: list[str]


def generate_brief(
    trend: RankedTrend,
    project: str,
    location: str,
    model_name: str,
) -> VideoBrief:
    """Use Gemini to synthesize a short-video brief and caption for a trend.

    Args:
        trend: The ranked cross-platform trend to build a brief for.
        project: Google Cloud project ID for Vertex AI.
        location: Vertex AI region (e.g. "us-central1").
        model_name: Gemini model name (e.g. "gemini-2.0-flash-001").

    Returns:
        A `VideoBrief` containing a scene description suitable for Veo 2
        plus an Instagram-ready caption and hashtags.
    """
    # TODO: init vertexai, prompt the model with the trend's topic/sources,
    # and parse the response into scene_description/caption/hashtags.
    vertexai.init(project=project, location=location)
    GenerativeModel(model_name)
    raise NotImplementedError
