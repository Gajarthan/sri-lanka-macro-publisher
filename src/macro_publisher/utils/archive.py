"""Helpers for keeping timestamped copies of generated outputs."""

from __future__ import annotations

import csv
import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path

from macro_publisher.config import ARCHIVE_DIR, FILE_HISTORY_PATH, REPO_ROOT
from macro_publisher.utils.dates import utc_now

FILE_HISTORY_COLUMNS = [
    "archive_timestamp",
    "archive_datetime_utc",
    "category",
    "source_path",
    "archive_path",
    "source_modified_datetime_utc",
    "size_bytes",
    "sha256",
]


def archive_output(
    path: Path,
    category: str,
    timestamp: datetime | None = None,
    *,
    archive_root: Path | None = None,
    manifest_path: Path | None = None,
    source_root: Path | None = None,
) -> Path | None:
    """Copy a generated file into the timestamped archive and log it in the manifest."""

    path = path.resolve()
    if not path.exists():
        return None

    source_root = (source_root or REPO_ROOT).resolve()
    try:
        relative_source = path.relative_to(source_root)
    except ValueError:
        return None

    archive_root = archive_root or ARCHIVE_DIR
    manifest_path = manifest_path or FILE_HISTORY_PATH
    archived_at = _normalize_timestamp(timestamp or utc_now())
    stamp = archived_at.strftime("%Y%m%dT%H%M%S%fZ")

    archive_path = (
        archive_root
        / category
        / relative_source.parent
        / f"{path.stem}__{stamp}{path.suffix}"
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, archive_path)

    stat = path.stat()
    source_modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    _append_manifest(
        manifest_path,
        {
            "archive_timestamp": str(int(archived_at.timestamp())),
            "archive_datetime_utc": archived_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "category": category,
            "source_path": relative_source.as_posix(),
            "archive_path": archive_path.resolve().relative_to(source_root).as_posix(),
            "source_modified_datetime_utc": source_modified.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "size_bytes": str(stat.st_size),
            "sha256": _sha256(path),
        },
    )
    return archive_path


def _append_manifest(path: Path, row: dict[str, str]) -> None:
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FILE_HISTORY_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("archive timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
