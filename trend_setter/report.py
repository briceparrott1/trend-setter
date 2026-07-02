"""Progressive on-disk run report.

`run_pipeline` used to only log/return what it generated after the whole
run (including publish) succeeded, so a failure at or after brief
generation (Kling clip failure, TTS failure, or the `posting/instagram.py`
`NotImplementedError` stub) left no record of the topic/script/caption/
shot_descriptions/citations that had already been produced. `RunReport`
rewrites a JSON file to disk on every stage completion so stages 1..N-1
survive a crash at stage N.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RunReport:
    """Accumulates run data and rewrites the full report to disk on every update."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, Any] = {}

    @classmethod
    def start(cls, output_dir: Path) -> RunReport:
        """Create a new timestamped report file for this run and write it now."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report = cls(output_dir / f"report_{timestamp}.json")
        report.update(status="started", started_at=datetime.datetime.now().isoformat())
        return report

    def update(self, **fields: Any) -> None:
        """Merge fields into the report and write the full report to disk now."""
        self._data.update(fields)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(self._data, indent=2, default=str))
        tmp_path.replace(self.path)
        logger.debug(
            "report %s updated: status=%s", self.path, self._data.get("status")
        )

    def record_failure(self, exc: BaseException) -> None:
        """Record that the run died, tagged with the last stage that completed."""
        last_stage = self._data.get("status", "unknown")
        self.update(
            status="failed",
            failed_after_stage=last_stage,
            error=f"{type(exc).__name__}: {exc}",
        )
