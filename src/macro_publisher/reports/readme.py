"""README generator wrapper."""

from __future__ import annotations

from pathlib import Path

from macro_publisher.reports.readme_dashboard import generate_readme_dashboard


def generate_readme(output: Path | None = None) -> Path:
    """Update the bounded README dashboard block."""

    return generate_readme_dashboard(output)
