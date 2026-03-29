from __future__ import annotations

from pathlib import Path

from macro_publisher.sources.dcs_ccpi import DCSCCPIAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_latest_release_prefers_latest_english_link() -> None:
    adapter = DCSCCPIAdapter()
    html = (FIXTURES / "dcs_monthly_ccpi_index.html").read_text(encoding="utf-8")

    release_code, release_url = adapter._latest_release(html)

    assert release_code == "20260227"
    assert release_url.endswith("/CCPI_20260227E")


def test_extract_latest_entry_from_movements_text() -> None:
    adapter = DCSCCPIAdapter()
    text = (FIXTURES / "dcs_movements_text.txt").read_text(encoding="utf-8")

    entry = adapter._extract_latest_entry(text)

    assert entry["reference_date"].isoformat() == "2026-02-28"
    assert entry["index_value"] == "195.3"
    assert entry["month_on_month_percent"] == "-0.9"
    assert entry["year_on_year_percent"] == "1.6"
