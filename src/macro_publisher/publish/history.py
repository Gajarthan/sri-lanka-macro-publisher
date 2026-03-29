"""History CSV publisher."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from macro_publisher.models import CanonicalRecord

HISTORY_COLUMNS = [
    "source",
    "indicator_code",
    "series_name",
    "category",
    "reference_date",
    "published_at",
    "collected_at",
    "value",
    "unit",
    "frequency",
    "currency",
    "market_scope",
    "source_url",
    "metadata",
]


def write_history(records: list[CanonicalRecord], output_dir: Path) -> list[Path]:
    """Write deduplicated history CSV files grouped by record history stem."""

    grouped: dict[str, list[CanonicalRecord]] = defaultdict(list)
    for record in records:
        grouped[record.history_file_stem()].append(record)

    written_paths: list[Path] = []
    for stem, grouped_records in grouped.items():
        path = output_dir / f"{stem}.csv"
        existing = _read_existing(path)
        for record in grouped_records:
            existing[record.logical_key] = _row_from_record(record)

        sorted_rows = sorted(
            existing.values(),
            key=lambda row: (
                row["reference_date"],
                row["indicator_code"],
                row["market_scope"],
                row["collected_at"],
            ),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS)
            writer.writeheader()
            writer.writerows(sorted_rows)
        written_paths.append(path)
    return written_paths


def _read_existing(path: Path) -> dict[tuple[str, str, str, str], dict[str, str]]:
    if not path.exists():
        return {}

    rows: dict[tuple[str, str, str, str], dict[str, str]] = {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (
                row["source"],
                row["indicator_code"],
                row["reference_date"],
                row["market_scope"],
            )
            rows[key] = row
    return rows


def _row_from_record(record: CanonicalRecord) -> dict[str, str]:
    return {
        "source": record.source,
        "indicator_code": record.indicator_code,
        "series_name": record.series_name,
        "category": record.category,
        "reference_date": record.reference_date.isoformat(),
        "published_at": record.published_at.isoformat() if record.published_at else "",
        "collected_at": record.collected_at.isoformat(),
        "value": str(record.value),
        "unit": record.unit,
        "frequency": record.frequency,
        "currency": record.currency or "",
        "market_scope": record.market_scope or "",
        "source_url": record.source_url,
        "metadata": json.dumps(record.metadata, sort_keys=True, ensure_ascii=False),
    }
