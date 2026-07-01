"""Entrypoint: loads config and starts the trend-setter scheduler."""

from __future__ import annotations

import argparse
import logging

from trend_setter.config import Settings
from trend_setter.scheduler import start


def main() -> None:
    """Parse CLI args, load settings, and start the scheduler."""
    parser = argparse.ArgumentParser(
        description=(
            "Monitor TikTok, YouTube, and Google Trends for rising topics, "
            "generate a Veo 2 video via Gemini, and post it to Instagram Reels."
        )
    )
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    settings = Settings()
    start(settings)


if __name__ == "__main__":
    main()
