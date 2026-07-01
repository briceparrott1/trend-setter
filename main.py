"""Entrypoint: loads config, runs the pipeline once, or starts the scheduler."""

from __future__ import annotations

import argparse
import asyncio
import logging

from trend_setter.config import Settings
from trend_setter.pipeline import run_pipeline
from trend_setter.scheduler import start

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse CLI args, load settings, and run once or start the scheduler."""
    parser = argparse.ArgumentParser(
        description=(
            "Monitor Google Trends, YouTube, and NewsData.io for rising topics, "
            "research a surprising angle via Perplexity Sonar, generate a "
            "narrated explainer video via Kling AI, and post it to Instagram Reels."
        )
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the pipeline once and exit, instead of starting the scheduler.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    settings = Settings()

    if args.run_once:
        result = asyncio.run(run_pipeline(settings))
        if result is None:
            logger.info("no trend candidates survived filtering this cycle")
        else:
            logger.info("pipeline run complete: %s", result)
        return

    start(settings)


if __name__ == "__main__":
    main()
