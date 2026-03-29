"""Bounded README dashboard generation from published data files."""

from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from macro_publisher.config import HISTORY_DIR, LATEST_DIR, REPO_ROOT, STATUS_PATH
from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.fs import write_text

BEGIN_MARKER = "<!-- BEGIN: DASHBOARD -->"
END_MARKER = "<!-- END: DASHBOARD -->"

SOURCE_ORDER = ("cbsl_fx", "dcs_ccpi", "doa_vegetable_prices")
SOURCE_PUBLICATION_CADENCE = {
    "cbsl_fx": "Business-day official FX rates from CBSL",
    "dcs_ccpi": "Monthly DCS CCPI release",
    "doa_vegetable_prices": "Daily DOA market prices",
}
PIPELINE_CHECK_CADENCE = {
    "cbsl_fx": "Every 3 hours on weekdays",
    "dcs_ccpi": "Daily at 02:30 UTC",
    "doa_vegetable_prices": "Daily at 01:15 UTC",
}
MAPPING_ROWS = (
    (
        "Latest snapshot",
        "`data/latest/cbsl_fx.json`, `data/latest/dcs_ccpi.json`, "
        "`data/latest/doa_vegetable_prices.json`",
    ),
    ("Source health", "`data/status.json`"),
    ("Exchange rates sample", "`data/history/usd_lkr_spot.csv`"),
    (
        "Vegetable prices sample",
        "`data/latest/doa_vegetable_prices.json` and "
        "`data/history/doa_vegetable_prices_pettah.csv`",
    ),
)
AUTO_GENERATED_NOTE = (
    "_Auto-generated from published data files. Do not edit inside this block manually._"
)


def generate_readme_dashboard(
    readme_path: Path | None = None,
    *,
    latest_dir: Path = LATEST_DIR,
    history_dir: Path = HISTORY_DIR,
    status_path: Path = STATUS_PATH,
) -> Path:
    """Update the bounded README dashboard block in place."""

    readme_path = readme_path or (REPO_ROOT / "README.md")
    original = _read_text(readme_path)
    block = render_dashboard_markdown(
        latest_dir=latest_dir,
        history_dir=history_dir,
        status_path=status_path,
    )
    updated = replace_dashboard_block(original, block)
    if updated != original:
        write_text(readme_path, updated)
        archive_output(readme_path, category="reports", timestamp=_dashboard_timestamp(status_path))
    return readme_path


def render_dashboard_markdown(
    *,
    latest_dir: Path = LATEST_DIR,
    history_dir: Path = HISTORY_DIR,
    status_path: Path = STATUS_PATH,
) -> str:
    """Render the deterministic README dashboard block body."""

    status_payload = _read_json(status_path)
    statuses = {item["source"]: item for item in status_payload["sources"]}

    fx_latest = _read_json(latest_dir / "cbsl_fx.json")
    ccpi_latest = _read_json(latest_dir / "dcs_ccpi.json")
    doa_latest = _read_json(latest_dir / "doa_vegetable_prices.json")
    usd_history = _read_csv(history_dir / "usd_lkr_spot.csv")

    pipeline_updated_at = max(
        [
            _parse_datetime(status["last_success_at"] or status["last_attempt_at"])
            for status in statuses.values()
        ]
        + [
            _parse_datetime(fx_latest["collected_at"]),
            _parse_datetime(ccpi_latest["collected_at"]),
            _parse_datetime(doa_latest["collected_at"]),
        ]
    )
    total_records = sum(status["record_count"] for status in statuses.values())

    fx_spot = _latest_record(fx_latest["records"], "usd_lkr_spot")
    ccpi_record = _latest_record(ccpi_latest["records"], "ccpi_colombo")
    doa_reference_date = max(record["reference_date"] for record in doa_latest["records"])
    doa_latest_records = [
        record
        for record in doa_latest["records"]
        if record["reference_date"] == doa_reference_date
    ]
    retail_values = [
        float(record["value"])
        for record in doa_latest_records
        if record.get("metadata", {}).get("price_type") == "retail"
    ]

    lines: list[str] = []
    append = lines.append
    append("## Published Data Dashboard")
    append("")
    append(AUTO_GENERATED_NOTE)
    append("")
    append(f"**Pipeline last updated (UTC):** {_format_utc(pipeline_updated_at)}  ")
    append(f"**Total published records:** {total_records:,}")
    append("")

    append("### Latest Snapshot")
    append("")
    append("| Metric | Latest value | Source reference date |")
    append("|--------|--------------|-----------------------|")
    append(
        f"| USD/LKR Spot | {float(fx_spot['value']):.3f} | {fx_spot['reference_date']} |"
    )
    append(
        f"| CCPI Colombo | {float(ccpi_record['value']):.1f} | {ccpi_record['reference_date']} |"
    )
    if retail_values:
        append(
            f"| Median vegetable retail | {median(retail_values):.0f} LKR/kg | "
            f"{doa_reference_date} |"
        )
    append("")

    append("### Inflation Summary")
    append("")
    append("| Measure | Value |")
    append("|---------|-------|")
    append(f"| CCPI level | {float(ccpi_record['value']):.1f} |")
    append(
        f"| Month-on-month | {ccpi_record['metadata'].get('month_on_month_percent', '-')}% |"
    )
    append(
        f"| Year-on-year | {ccpi_record['metadata'].get('year_on_year_percent', '-')}% |"
    )
    append(
        "| 12-month moving average | "
        f"{ccpi_record['metadata'].get('twelve_month_moving_average_percent', '-')}% |"
    )
    append(f"| Source publication date | {_format_source_datetime(ccpi_record['published_at'])} |")
    append(f"| Source reference month | {ccpi_record['reference_date']} |")
    append("")

    append("### Source Health")
    append("")
    append(
        "| Source | Status | Pipeline updated at (UTC) | Source reference date | Records |"
    )
    append(
        "|--------|--------|---------------------------|-----------------------|---------|"
    )
    for source_name in SOURCE_ORDER:
        status = statuses[source_name]
        last_update = _parse_datetime(status["last_success_at"] or status["last_attempt_at"])
        append(
            f"| {source_name} | {_status_label(status)} | {_format_utc(last_update)} | "
            f"{status['last_reference_date'] or '-'} | {status['record_count']:,} |"
        )
    append("")

    append("### Exchange Rates Sample")
    append("")
    append("| Date | USD/LKR spot |")
    append("|------|--------------|")
    for row in list(reversed(usd_history[-5:])):
        append(f"| {row['reference_date']} | {float(row['value']):.3f} |")
    append("")

    append("### Vegetable Prices Sample")
    append("")
    append(f"_Source reference date: {doa_reference_date}_")
    append("")
    append("| Item | Market | Price type | LKR/kg |")
    append("|------|--------|------------|--------|")
    for record in _vegetable_sample_rows(doa_latest_records):
        append(
            f"| {record['item']} | {record['market']} | {record['price_type']} | "
            f"{record['value']:.0f} |"
        )
    append("")

    append("### Dashboard-to-File Mapping")
    append("")
    append("| Dashboard section | Published file inputs |")
    append("|-------------------|-----------------------|")
    for section, files in MAPPING_ROWS:
        append(f"| {section} | {files} |")
    append("")

    append("### Freshness and Cadence")
    append("")
    append(
        "| Source | Source publication cadence | Pipeline check cadence | Freshness note |"
    )
    append(
        "|--------|----------------------------|------------------------|----------------|"
    )
    for source_name in SOURCE_ORDER:
        append(
            f"| {source_name} | {SOURCE_PUBLICATION_CADENCE[source_name]} | "
            f"{PIPELINE_CHECK_CADENCE[source_name]} | "
            "Reference date may lag the pipeline update timestamp. |"
        )
    append("")
    append(
        "Pipeline last updated is the most recent successful collection time in the "
        "published status files."
    )
    append(
        "Source reference date is the economic observation date, which is distinct from "
        "pipeline execution time."
    )
    return "\n".join(lines)


def replace_dashboard_block(readme_text: str, dashboard_body: str) -> str:
    """Replace only the bounded dashboard block in README text."""

    pattern = re.compile(
        rf"{re.escape(BEGIN_MARKER)}\n.*?\n{re.escape(END_MARKER)}",
        flags=re.DOTALL,
    )
    replacement = f"{BEGIN_MARKER}\n{dashboard_body.rstrip()}\n{END_MARKER}"
    updated, count = pattern.subn(replacement, readme_text, count=1)
    if count != 1:
        raise ValueError(
            f"README markers {BEGIN_MARKER!r} and {END_MARKER!r} must appear exactly once."
        )
    return updated


def _dashboard_timestamp(status_path: Path) -> datetime:
    payload = _read_json(status_path)
    return max(
        _parse_datetime(item["last_success_at"] or item["last_attempt_at"])
        for item in payload["sources"]
    )


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required published data file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required published data file is missing: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"README file is missing: {path}")
    return path.read_text(encoding="utf-8")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def _format_source_datetime(value: str | None) -> str:
    if not value:
        return "-"
    dt = _parse_datetime(value)
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def _latest_record(records: list[dict], indicator_code: str) -> dict:
    matching = [record for record in records if record["indicator_code"] == indicator_code]
    if not matching:
        raise ValueError(f"Indicator {indicator_code!r} not found in published data.")
    return max(
        matching,
        key=lambda record: (record["reference_date"], record["collected_at"]),
    )


def _status_label(status: dict) -> str:
    return "ok" if status["ok"] else f"error: {status['error'] or 'unknown'}"


def _vegetable_sample_rows(records: list[dict]) -> list[dict[str, str | float]]:
    rows = []
    for record in records:
        metadata = record.get("metadata", {})
        if metadata.get("price_type") != "wholesale":
            continue
        if record.get("market_scope", "") != "Pettah market":
            continue
        rows.append(
            {
                "item": metadata.get("item", ""),
                "market": "Pettah",
                "price_type": "wholesale",
                "value": float(record["value"]),
            }
        )
    if not rows:
        raise ValueError("No Pettah wholesale vegetable records found for the latest snapshot.")
    return sorted(rows, key=lambda row: str(row["item"]))[:8]
