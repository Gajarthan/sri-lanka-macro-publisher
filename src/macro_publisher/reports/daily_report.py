"""Generate DAILY_REPORT.md from pipeline history and current data."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from macro_publisher.config import (
    HISTORY_DIR,
    LATEST_DIR,
    REPO_ROOT,
    STATUS_PATH,
)
from macro_publisher.reports.pipeline_history import read_history
from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.fs import write_text


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def generate_daily_report(output: Path | None = None) -> Path:
    """Generate DAILY_REPORT.md with trend data and day-over-day changes."""

    output = output or (REPO_ROOT / "DAILY_REPORT.md")
    now = utc_now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    status = _load_json(STATUS_PATH)
    history = read_history()

    lines: list[str] = []
    w = lines.append

    w("# Daily Report")
    w("")
    w(f"*Generated: {timestamp}*")
    w("")

    # Current totals
    total_records = sum(s["record_count"] for s in status["sources"])
    sources_ok = sum(1 for s in status["sources"] if s["ok"])
    w("## Current Totals")
    w("")
    w(f"- **{total_records:,}** total records across all sources")
    w(f"- **{sources_ok}/{len(status['sources'])}** sources healthy")
    for source in status["sources"]:
        ref = source["last_reference_date"] or "unknown"
        w(f"- **{source['source']}**: {source['record_count']:,} records (latest: {ref})")
    w("")

    # Pipeline run history table (last 30 entries)
    if history:
        w("## Pipeline Run History (Last 30 Runs)")
        w("")
        w("| Timestamp | Sources OK | Total Records | CBSL FX | DCS CCPI | DOA |")
        w("|-----------|------------|---------------|---------|----------|-----|")
        for row in history[-30:]:
            w(
                f"| {row['datetime_utc']} "
                f"| {row['sources_ok']}/{row['sources_total']} "
                f"| {int(row['total_records']):,} "
                f"| {int(row['cbsl_fx_records']):,} "
                f"| {int(row['dcs_ccpi_records']):,} "
                f"| {int(row['doa_records']):,} |"
            )
        w("")

    # Day-over-day changes from pipeline history
    if len(history) >= 2:
        w("## Day-over-Day Changes")
        w("")
        latest = history[-1]
        previous = history[-2]
        delta_records = int(latest["total_records"]) - int(previous["total_records"])
        delta_sign = "+" if delta_records >= 0 else ""
        w(f"- Total records: {delta_sign}{delta_records:,}")

        for source_key, label in [
            ("cbsl_fx_records", "CBSL FX"),
            ("dcs_ccpi_records", "DCS CCPI"),
            ("doa_records", "DOA Vegetables"),
        ]:
            delta = int(latest[source_key]) - int(previous[source_key])
            sign = "+" if delta >= 0 else ""
            w(f"- {label}: {sign}{delta:,}")

        ref_changes = []
        for source_key, label in [
            ("cbsl_fx_ref_date", "CBSL FX"),
            ("dcs_ccpi_ref_date", "DCS CCPI"),
            ("doa_ref_date", "DOA"),
        ]:
            if latest[source_key] != previous[source_key]:
                ref_changes.append(
                    f"- {label} reference date: {previous[source_key]} -> {latest[source_key]}"
                )
        if ref_changes:
            w("")
            w("**Reference date changes:**")
            for change in ref_changes:
                w(change)
        w("")

    # Exchange rate trend (last 7 days)
    spot_rows = _read_csv(HISTORY_DIR / "usd_lkr_spot.csv")
    if spot_rows:
        recent_spot = spot_rows[-7:]
        w("## USD/LKR Spot Trend (Last 7 Days)")
        w("")
        w("| Date | Rate | Change |")
        w("|------|------|--------|")
        prev_val = None
        for row in recent_spot:
            val = float(row["value"])
            if prev_val is not None:
                delta = val - prev_val
                sign = "+" if delta >= 0 else ""
                change = f"{sign}{delta:.3f}"
            else:
                change = "-"
            w(f"| {row['reference_date']} | {val:.3f} | {change} |")
            prev_val = val
        w("")

    # Vegetable price highlights
    doa_latest = _load_json(LATEST_DIR / "doa_vegetable_prices.json")
    doa_latest_date = max(
        (r["reference_date"] for r in doa_latest["records"]), default=""
    )
    movers: list[tuple[str, float, float]] = []
    for r in doa_latest["records"]:
        if r["reference_date"] != doa_latest_date:
            continue
        yesterday = r.get("metadata", {}).get("yesterday_value")
        if yesterday is None:
            continue
        delta = float(r["value"]) - float(yesterday)
        if abs(delta) > 0:
            movers.append((r["series_name"], float(r["value"]), delta))

    if movers:
        movers.sort(key=lambda x: abs(x[2]), reverse=True)
        w("## Top Price Movers (Today)")
        w("")
        w("| Series | Price | Daily Change |")
        w("|--------|-------|--------------|")
        for name, price, delta in movers[:10]:
            sign = "+" if delta >= 0 else ""
            w(f"| {name} | {price:.0f} | {sign}{delta:.0f} |")
        w("")

    # Footer
    w("---")
    w("")
    w(f"*Report covers data through {timestamp}*")
    w("")

    content = "\n".join(lines)
    write_text(output, content)
    archive_output(output, category="reports", timestamp=now)
    return output
