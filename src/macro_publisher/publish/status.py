"""Status file management."""

from __future__ import annotations

import json
from pathlib import Path

from macro_publisher.models import SourceStatus
from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.fs import write_json


def read_statuses(path: Path) -> dict[str, SourceStatus]:
    """Read the persisted status file if it exists."""

    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    statuses = {}
    for item in payload.get("sources", []):
        status = SourceStatus.model_validate(item)
        statuses[status.source] = status
    return statuses


def write_statuses(path: Path, statuses: dict[str, SourceStatus]) -> None:
    """Write the consolidated source status file."""

    payload = {"sources": [statuses[key].model_dump(mode="json") for key in sorted(statuses)]}
    write_json(path, payload)
    timestamp = max((status.last_attempt_at for status in statuses.values()), default=utc_now())
    archive_output(path, category="status", timestamp=timestamp)
