from __future__ import annotations

from datetime import UTC, datetime

import pytest

from macro_publisher.models import CanonicalRecord, Category, Frequency, SourceCode


def test_canonical_record_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValueError):
        CanonicalRecord(
            indicator_code="usd_lkr_spot",
            series_name="USD/LKR Spot Indicative Exchange Rate",
            category=Category.EXCHANGE_RATE,
            source=SourceCode.CBSL,
            source_url="https://example.com",
            value="314.22",
            unit="LKR per USD",
            frequency=Frequency.BUSINESS_DAILY,
            reference_date="2026-03-27",
            collected_at=datetime(2026, 3, 29, 8, 0, 0),
        )


def test_canonical_record_serializes_decimal_as_number() -> None:
    record = CanonicalRecord(
        indicator_code="usd_lkr_spot",
        series_name="USD/LKR Spot Indicative Exchange Rate",
        category=Category.EXCHANGE_RATE,
        source=SourceCode.CBSL,
        source_url="https://example.com",
        value="314.22",
        unit="LKR per USD",
        frequency=Frequency.BUSINESS_DAILY,
        reference_date="2026-03-27",
        collected_at=datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
    )

    dumped = record.model_dump(mode="json")
    assert dumped["value"] == 314.22
