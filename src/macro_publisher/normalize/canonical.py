"""Helpers for building canonical records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from macro_publisher.models import CanonicalRecord, Category, Frequency, SourceCode


def build_record(
    *,
    indicator_code: str,
    series_name: str,
    category: Category,
    source: SourceCode,
    source_url: str,
    value: Decimal | str | float,
    unit: str,
    frequency: Frequency,
    reference_date: date,
    collected_at: datetime,
    published_at: datetime | None = None,
    market_scope: str | None = None,
    currency: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CanonicalRecord:
    """Construct a canonical record with a minimal call-site footprint."""

    return CanonicalRecord(
        indicator_code=indicator_code,
        series_name=series_name,
        category=category,
        source=source,
        source_url=source_url,
        value=Decimal(str(value)),
        unit=unit,
        frequency=frequency,
        reference_date=reference_date,
        published_at=published_at,
        collected_at=collected_at,
        market_scope=market_scope,
        currency=currency,
        metadata=metadata or {},
    )
