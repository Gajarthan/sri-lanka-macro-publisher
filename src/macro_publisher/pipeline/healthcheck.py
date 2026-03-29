"""Source healthcheck helpers."""

from __future__ import annotations

from macro_publisher.models import SourceStatus
from macro_publisher.sources import SOURCE_REGISTRY
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.http import build_http_client


def healthcheck() -> list[SourceStatus]:
    """Run source collectors without writing files."""

    statuses: list[SourceStatus] = []
    with build_http_client() as client:
        for source_name, adapter_cls in SOURCE_REGISTRY.items():
            attempted_at = utc_now()
            try:
                dataset = adapter_cls().healthcheck(client)
                statuses.append(
                    SourceStatus(
                        source=source_name,
                        ok=True,
                        last_attempt_at=attempted_at,
                        last_success_at=attempted_at,
                        last_reference_date=max(record.reference_date for record in dataset.records)
                        if dataset.records
                        else None,
                        record_count=len(dataset.records),
                    )
                )
            except Exception as exc:
                statuses.append(
                    SourceStatus(
                        source=source_name,
                        ok=False,
                        last_attempt_at=attempted_at,
                        error=str(exc),
                    )
                )
    return statuses
