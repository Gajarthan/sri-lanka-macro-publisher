"""Run all sources."""

from __future__ import annotations

import logging

from macro_publisher.pipeline.run_source import run_source
from macro_publisher.sources import SOURCE_REGISTRY

logger = logging.getLogger(__name__)


def run_all() -> list:
    """Run every registered source, record a history row, and return statuses."""

    statuses = [run_source(source_name) for source_name in SOURCE_REGISTRY]

    try:
        from macro_publisher.reports.pipeline_history import append_run

        append_run()
    except Exception:
        logger.warning("Failed to append pipeline history row", exc_info=True)

    return statuses
