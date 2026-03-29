from __future__ import annotations

from datetime import UTC, datetime

from macro_publisher.models import Category, Frequency, SourceCode, SourceDataset, SourceStatus
from macro_publisher.normalize.canonical import build_record
from macro_publisher.publish.history import write_history
from macro_publisher.publish.latest import write_latest_dataset, write_normalized_snapshot
from macro_publisher.publish.status import read_statuses, write_statuses


def build_sample_record():
    return build_record(
        indicator_code="usd_lkr_spot",
        series_name="USD/LKR Spot Indicative Exchange Rate",
        category=Category.EXCHANGE_RATE,
        source=SourceCode.CBSL,
        source_url="https://www.cbsl.gov.lk/example",
        value="314.22",
        unit="LKR per USD",
        frequency=Frequency.BUSINESS_DAILY,
        reference_date="2026-03-27",
        collected_at=datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
        market_scope="Sri Lanka interbank",
    )


def test_publishers_write_expected_shapes(tmp_path) -> None:
    record = build_sample_record()
    dataset = SourceDataset(
        source_name="cbsl_fx",
        source=SourceCode.CBSL,
        family_code="cbsl_fx",
        family_name="CBSL exchange rates",
        source_urls=["https://www.cbsl.gov.lk/example"],
        collected_at=datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
        records=[record],
    )

    latest_path = write_latest_dataset(dataset, tmp_path / "latest")
    normalized_path = write_normalized_snapshot(dataset, tmp_path / "normalized")
    history_paths = write_history([record], tmp_path / "history")

    assert latest_path.exists()
    assert normalized_path.exists()
    assert history_paths[0].name == "usd_lkr_spot.csv"
    assert "usd_lkr_spot" in latest_path.read_text(encoding="utf-8")


def test_status_round_trip(tmp_path) -> None:
    path = tmp_path / "status.json"
    status = SourceStatus(
        source="cbsl_fx",
        ok=True,
        last_attempt_at=datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
        last_success_at=datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
        last_reference_date="2026-03-27",
        record_count=1,
        content_hash="abc123",
    )

    write_statuses(path, {"cbsl_fx": status})
    loaded = read_statuses(path)

    assert loaded["cbsl_fx"].record_count == 1
