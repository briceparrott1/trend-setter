"""Video generation abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod


class VideoGenProvider(ABC):
    """Interface a concrete video-generation backend (e.g. Kling AI) implements.

    Kept separate from any single provider's module so the underlying model
    can be swapped without touching pipeline code.
    """

    @abstractmethod
    async def generate_clip(self, brief: str, duration_seconds: int = 5) -> bytes: ...

    @abstractmethod
    async def generate_video(self, clips: list[str]) -> bytes: ...
