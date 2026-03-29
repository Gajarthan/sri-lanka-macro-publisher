from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from macro_publisher.sources.doa_vegetable_prices import DOAVegetablePricesAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_item_records_preserves_market_scope_and_grouping() -> None:
    adapter = DOAVegetablePricesAdapter()
    payload = json.loads((FIXTURES / "doa_beans.json").read_text(encoding="utf-8"))

    records = adapter._build_item_records(
        "Beans",
        "https://infohub.doa.gov.lk/vegetable-prices-all/?item=Beans#vegchart",
        payload,
        datetime(2026, 3, 29, 8, 0, 0, tzinfo=UTC),
    )

    assert len(records) == 8
    assert records[0].market_scope == "Pettah market"
    assert records[0].metadata["history_file"] == "doa_vegetable_prices_pettah"
    assert records[-1].market_scope == "Dambulla Dedicated Economic Centre"
