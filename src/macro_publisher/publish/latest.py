"""Write latest and normalized source outputs."""

from __future__ import annotations

import json
from pathlib import Path

from macro_publisher.models import SourceDataset
from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.fs import write_json, write_text


def write_latest_dataset(dataset: SourceDataset, output_dir: Path) -> Path:
    """Write the latest source snapshot as JSON."""

    payload = {
        "family_code": dataset.family_code,
        "family_name": dataset.family_name,
        "source": dataset.source,
        "source_name": dataset.source_name,
        "collected_at": dataset.collected_at.isoformat(),
        "record_count": len(dataset.records),
        "source_urls": dataset.source_urls,
        "metadata": dataset.metadata,
        "records": [record.model_dump(mode="json") for record in dataset.records],
    }
    path = output_dir / f"{dataset.family_code}.json"
    write_json(path, payload)
    archive_output(path, category="latest", timestamp=dataset.collected_at)
    return path


def write_normalized_snapshot(dataset: SourceDataset, output_dir: Path) -> Path:
    """Write normalized canonical records as JSON Lines."""

    path = output_dir / f"{dataset.family_code}.jsonl"
    lines = [
        json.dumps(record.model_dump(mode="json"), sort_keys=True)
        for record in dataset.records
    ]
    write_text(path, "\n".join(lines) + ("\n" if lines else ""))
    archive_output(path, category="normalized", timestamp=dataset.collected_at)
    return path
