from __future__ import annotations

from pathlib import Path

from macro_publisher.sources.cbsl_fx import CBSLFXAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_spot_table_fixture() -> None:
    adapter = CBSLFXAdapter()
    html = (FIXTURES / "cbsl_spot_results.html").read_text(encoding="utf-8")

    parsed = adapter._parse_tables(html)

    assert "US Dollar" in parsed
    assert parsed["US Dollar"][-1][0].isoformat() == "2026-03-27"
    assert str(parsed["US Dollar"][-1][1]) == "314.3860"


def test_parse_tt_table_fixture() -> None:
    adapter = CBSLFXAdapter()
    html = (FIXTURES / "cbsl_tt_results.html").read_text(encoding="utf-8")

    parsed = adapter._parse_tt_tables(html)

    assert parsed["United States Dollar"][-1][0].isoformat() == "2026-03-27"
    assert str(parsed["United States Dollar"][-1][1]) == "310.6542"
    assert str(parsed["United States Dollar"][-1][2]) == "318.1938"
