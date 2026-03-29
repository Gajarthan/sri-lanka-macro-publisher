"""Validation helpers for canonical records."""

from __future__ import annotations

from collections.abc import Iterable

from macro_publisher.models import CanonicalRecord


def validate_records(records: Iterable[CanonicalRecord]) -> list[CanonicalRecord]:
    """Validate a collection of records and reject duplicate logical keys."""

    validated = list(records)
    seen: set[tuple[str, str, str, str]] = set()
    for record in validated:
        if not record.series_name.strip():
            raise ValueError("series_name must not be blank")
        if record.logical_key in seen:
            raise ValueError(f"duplicate logical key detected: {record.logical_key}")
        seen.add(record.logical_key)
    return validated
