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
            "Monitor Google Trends, YouTube, and NewsData.io for rising topics, "
            "research a surprising angle via Perplexity Sonar, generate a "
            "narrated explainer video via Kling AI, and post it to Instagram Reels."
        )
    )
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    settings = Settings()
    start(settings)


if __name__ == "__main__":
    main()
