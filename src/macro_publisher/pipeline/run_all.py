"""Run all sources."""

from __future__ import annotations

from macro_publisher.pipeline.run_source import run_source
from macro_publisher.sources import SOURCE_REGISTRY


def run_all() -> list:
    """Run every registered source and return statuses."""

    return [run_source(source_name) for source_name in SOURCE_REGISTRY]
