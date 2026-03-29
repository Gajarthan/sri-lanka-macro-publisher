from __future__ import annotations

import csv
from datetime import UTC, datetime

from macro_publisher.utils.archive import archive_output


def test_archive_output_copies_file_and_updates_manifest(tmp_path) -> None:
    source_root = tmp_path / "repo"
    source_path = source_root / "docs" / "readme-assets" / "chart.png"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(b"png-data")

    archive_root = source_root / "data" / "archives"
    manifest_path = source_root / "data" / "file_history.csv"
    archived = archive_output(
        source_path,
        category="charts",
        timestamp=datetime(2026, 3, 29, 9, 30, 0, tzinfo=UTC),
        archive_root=archive_root,
        manifest_path=manifest_path,
        source_root=source_root,
    )

    assert archived is not None
    assert archived.exists()
    assert archived.read_bytes() == b"png-data"
    assert "20260329T093000000000Z" in archived.name

    with manifest_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["category"] == "charts"
    assert rows[0]["source_path"] == "docs/readme-assets/chart.png"
    assert rows[0]["archive_path"].endswith(archived.name)
