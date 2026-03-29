"""Run a single source end to end."""

from __future__ import annotations

from macro_publisher.config import HISTORY_DIR, LATEST_DIR, NORMALIZED_DIR, STATUS_PATH
from macro_publisher.models import SourceStatus
from macro_publisher.publish.history import write_history
from macro_publisher.publish.latest import write_latest_dataset, write_normalized_snapshot
from macro_publisher.publish.status import read_statuses, write_statuses
from macro_publisher.sources import SOURCE_REGISTRY
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.hashing import stable_hash
from macro_publisher.utils.http import build_http_client
from macro_publisher.validators import validate_records


def run_source(source_name: str, *, write_outputs: bool = True) -> SourceStatus:
    """Run a source adapter and optionally publish outputs."""

    if source_name not in SOURCE_REGISTRY:
        available = ", ".join(sorted(SOURCE_REGISTRY))
        raise KeyError(f"Unknown source {source_name!r}. Available sources: {available}")

    adapter = SOURCE_REGISTRY[source_name]()
    statuses = read_statuses(STATUS_PATH)
    attempted_at = utc_now()

    with build_http_client() as client:
        try:
            dataset = adapter.collect(client)
            dataset.records = validate_records(dataset.records)
            if write_outputs:
                write_latest_dataset(dataset, LATEST_DIR)
                write_normalized_snapshot(dataset, NORMALIZED_DIR)
                write_history(dataset.records, HISTORY_DIR)

            content_hash = stable_hash(
                [record.model_dump(mode="json") for record in dataset.records]
            )
            status = SourceStatus(
                source=source_name,
                ok=True,
                last_attempt_at=attempted_at,
                last_success_at=attempted_at,
                last_reference_date=max(record.reference_date for record in dataset.records)
                if dataset.records
                else None,
                record_count=len(dataset.records),
                content_hash=content_hash,
            )
        except Exception as exc:
            previous = statuses.get(source_name)
            status = SourceStatus(
                source=source_name,
                ok=False,
                last_attempt_at=attempted_at,
                last_success_at=previous.last_success_at if previous else None,
                last_reference_date=previous.last_reference_date if previous else None,
                record_count=previous.record_count if previous else 0,
                error=str(exc),
                content_hash=previous.content_hash if previous else None,
            )
            statuses[source_name] = status
            if write_outputs:
                write_statuses(STATUS_PATH, statuses)
            raise

    statuses[source_name] = status
    if write_outputs:
        write_statuses(STATUS_PATH, statuses)
    return status
