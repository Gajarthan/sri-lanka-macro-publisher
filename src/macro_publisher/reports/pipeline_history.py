"""Track aggregate pipeline stats per run in a CSV time series."""

from __future__ import annotations

import csv
from pathlib import Path

from macro_publisher.config import PIPELINE_HISTORY_PATH, STATUS_PATH
from macro_publisher.publish.status import read_statuses
from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.dates import utc_now

HISTORY_COLUMNS = [
    "timestamp",
    "datetime_utc",
    "sources_ok",
    "sources_total",
    "total_records",
    "cbsl_fx_records",
    "dcs_ccpi_records",
    "doa_records",
    "cbsl_fx_ref_date",
    "dcs_ccpi_ref_date",
    "doa_ref_date",
]


def append_run(path: Path | None = None) -> Path:
    """Append one row summarising the current pipeline state to the history CSV."""

    path = path or PIPELINE_HISTORY_PATH
    statuses = read_statuses(STATUS_PATH)

    now = utc_now()
    sources_ok = sum(1 for s in statuses.values() if s.ok)
    total_records = sum(s.record_count for s in statuses.values())

    def _ref(name: str) -> str:
        s = statuses.get(name)
        return s.last_reference_date.isoformat() if s and s.last_reference_date else ""

    def _count(name: str) -> int:
        s = statuses.get(name)
        return s.record_count if s else 0

    row = {
        "timestamp": str(int(now.timestamp())),
        "datetime_utc": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sources_ok": str(sources_ok),
        "sources_total": str(len(statuses)),
        "total_records": str(total_records),
        "cbsl_fx_records": str(_count("cbsl_fx")),
        "dcs_ccpi_records": str(_count("dcs_ccpi")),
        "doa_records": str(_count("doa_vegetable_prices")),
        "cbsl_fx_ref_date": _ref("cbsl_fx"),
        "dcs_ccpi_ref_date": _ref("dcs_ccpi"),
        "doa_ref_date": _ref("doa_vegetable_prices"),
    }

    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    archive_output(path, category="history", timestamp=now)
    return path


def read_history(path: Path | None = None) -> list[dict[str, str]]:
    """Read the full pipeline history CSV."""

    path = path or PIPELINE_HISTORY_PATH
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
