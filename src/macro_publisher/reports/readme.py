"""Auto-generate README.md from the current published data."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from statistics import median

from macro_publisher.config import (
    HISTORY_DIR,
    LATEST_DIR,
    README_ASSETS_DIR,
    REPO_ROOT,
    STATUS_PATH,
)
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


def _fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def generate_readme(output: Path | None = None) -> Path:
    """Generate README.md from the current data directory state."""

    output = output or (REPO_ROOT / "README.md")
    now = utc_now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    status = _load_json(STATUS_PATH)
    fx_latest = _load_json(LATEST_DIR / "cbsl_fx.json")
    ccpi_latest = _load_json(LATEST_DIR / "dcs_ccpi.json")
    doa_latest = _load_json(LATEST_DIR / "doa_vegetable_prices.json")

    # Extract key metrics
    fx_spot = next(
        (r for r in fx_latest["records"] if r["indicator_code"] == "usd_lkr_spot"), None
    )
    ccpi_record = ccpi_latest["records"][0] if ccpi_latest["records"] else None

    doa_latest_date = max(
        (r["reference_date"] for r in doa_latest["records"]), default=""
    )
    doa_latest_records = [
        r for r in doa_latest["records"] if r["reference_date"] == doa_latest_date
    ]
    retail_values = [
        float(r["value"])
        for r in doa_latest_records
        if r.get("metadata", {}).get("price_type") == "retail"
    ]

    all_ok = all(s["ok"] for s in status["sources"])
    total_records = sum(s["record_count"] for s in status["sources"])

    lines: list[str] = []
    w = lines.append

    # Header and badges
    w("# Sri Lanka Macro Publisher")
    w("")
    ts_badge = timestamp.replace(" ", "_").replace(":", "%3A")
    w(f"![LastUpdated](https://img.shields.io/badge/last_updated-{ts_badge}-green)")
    w(f"![Sources](https://img.shields.io/badge/sources-{len(status['sources'])}_active-blue)")
    health_color = "brightgreen" if all_ok else "red"
    health_label = "all_green" if all_ok else "review"
    w(f"![Health](https://img.shields.io/badge/health-{health_label}-{health_color})")
    w("")

    # Dashboard summary
    w("## Dashboard Overview")
    w("")
    dashboard_rows = [
        (
            "Overview",
            "Current pipeline state across all official sources",
            "Health badges, latest snapshot, total records",
        ),
        (
            "Exchange Rates",
            "LKR performance across major currencies",
            "USD/LKR spot, indicative rates, TT buy/sell spreads",
        ),
        (
            "Inflation",
            "Colombo consumer price trend",
            "CCPI level, month-on-month, year-on-year, 12-month average",
        ),
        (
            "Commodity Prices",
            "Daily vegetable market movement",
            "Pettah and Dambulla pricing, item heatmap, market comparison",
        ),
    ]
    w("| View | Focus | Key Signals |")
    w("|------|-------|-------------|")
    for view, focus, signals in dashboard_rows:
        w(f"| {view} | {focus} | {signals} |")
    w("")

    # About section
    w("## About")
    w("")
    w("Static-data publishing pipeline for official Sri Lankan macroeconomic datasets. "
      "Fetches data from official public sources, normalizes observations into a canonical "
      "schema, validates records, and writes machine-readable JSON and CSV outputs into "
      "Git-tracked files.")
    w("")
    w("**Data Sources:** CBSL, DCS, DOA (official government publications)")
    w("")
    w("**Update Frequency:** CBSL FX every 3 hours on weekdays, DOA daily, DCS CCPI daily")
    w("")

    # Snapshot section
    w("## Latest Snapshot")
    w("")
    w(f"**Last updated:** {timestamp}")
    w(f"**Total records:** {total_records:,}")
    w("")

    # Key metrics table
    w("| Metric | Value | Reference Date |")
    w("|--------|-------|----------------|")
    if fx_spot:
        w(f"| USD/LKR Spot | {float(fx_spot['value']):.3f} | {fx_spot['reference_date']} |")
    if ccpi_record:
        w(f"| CCPI Colombo | {float(ccpi_record['value']):.1f} | {ccpi_record['reference_date']} |")
    if retail_values:
        w(f"| Median Veg Retail | {median(retail_values):.0f} LKR/kg | {doa_latest_date} |")
    w("")

    # Inflation cards
    if ccpi_record:
        meta = ccpi_record.get("metadata", {})
        w("## Inflation")
        w("")
        w("| Measure | Value |")
        w("|---------|-------|")
        w(f"| CCPI Level | {float(ccpi_record['value']):.1f} |")
        if meta.get("month_on_month_percent"):
            w(f"| Month-on-Month | {meta['month_on_month_percent']}% |")
        if meta.get("year_on_year_percent"):
            w(f"| Year-on-Year | {meta['year_on_year_percent']}% |")
        if meta.get("twelve_month_moving_average_percent"):
            w(f"| 12-Month Moving Avg | {meta['twelve_month_moving_average_percent']}% |")
        w("")

    # Charts
    charts_dir = README_ASSETS_DIR
    if (charts_dir / "fx_trend.png").exists():
        w("## Charts")
        w("")
        w("### Exchange Rate Trend")
        w("")
        w("![USD/LKR Trend](docs/readme-assets/fx_trend.png)")
        w("")
        w("### Multi-Currency Comparison")
        w("")
        w("![Multi-Currency](docs/readme-assets/multi_currency.png)")
        w("")
        w("### TT Buy/Sell Spreads")
        w("")
        w("![TT Spreads](docs/readme-assets/tt_spreads.png)")
        w("")
    if (charts_dir / "inflation_trend.png").exists():
        w("### Inflation Trend")
        w("")
        w("![CCPI Trend](docs/readme-assets/inflation_trend.png)")
        w("")
    if (charts_dir / "vegetable_heatmap.png").exists():
        w("### Vegetable Price Heatmap")
        w("")
        w("![Vegetable Heatmap](docs/readme-assets/vegetable_heatmap.png)")
        w("")
    if (charts_dir / "market_comparison.png").exists():
        w("### Market Comparison")
        w("")
        w("![Market Comparison](docs/readme-assets/market_comparison.png)")
        w("")

    # Exchange rates table
    spot_rows = _read_csv(HISTORY_DIR / "usd_lkr_spot.csv")
    if spot_rows:
        w("## Exchange Rates (USD/LKR Spot)")
        w("")
        recent = spot_rows[-10:]
        w("| Date | Rate |")
        w("|------|------|")
        for row in reversed(recent):
            w(f"| {row['reference_date']} | {float(row['value']):.3f} |")
        w("")

    # Multi-currency latest
    currencies = [
        ("USD", "usd_lkr_indicative.csv"),
        ("EUR", "eur_lkr_indicative.csv"),
        ("GBP", "gbp_lkr_indicative.csv"),
        ("JPY", "jpy_lkr_indicative.csv"),
        ("AUD", "aud_lkr_indicative.csv"),
        ("CNY", "cny_lkr_indicative.csv"),
    ]
    currency_latest = []
    for label, filename in currencies:
        rows = _read_csv(HISTORY_DIR / filename)
        if rows:
            last = rows[-1]
            currency_latest.append((label, float(last["value"]), last["reference_date"]))

    if currency_latest:
        w("## Major Currencies (Indicative Rates)")
        w("")
        w("| Currency | LKR Rate | Date |")
        w("|----------|----------|------|")
        for label, value, ref_date in currency_latest:
            w(f"| {label} | {value:.2f} | {ref_date} |")
        w("")

    # Vegetable prices - latest snapshot
    if doa_latest_records:
        items_seen: dict[str, dict] = {}
        for r in doa_latest_records:
            meta = r.get("metadata", {})
            item = meta.get("item", "")
            price_type = meta.get("price_type", "")
            market = r.get("market_scope", "")
            key = f"{item}_{market}_{price_type}"
            if key not in items_seen:
                items_seen[key] = {
                    "item": item,
                    "market": market,
                    "price_type": price_type,
                    "value": float(r["value"]),
                }

        w("## Vegetable Prices (Latest)")
        w("")
        w(f"*Reference date: {doa_latest_date}*")
        w("")

        for market_name in ["Pettah market", "Dambulla market"]:
            market_items = [
                v for v in items_seen.values()
                if v["market"] == market_name and v["price_type"] == "wholesale"
            ]
            if market_items:
                short_name = market_name.replace(" market", "")
                w(f"### {short_name} Wholesale")
                w("")
                w("| Item | Price (LKR/kg) |")
                w("|------|----------------|")
                for item in sorted(market_items, key=lambda x: x["item"]):
                    w(f"| {item['item']} | {item['value']:.0f} |")
                w("")

    # Source health
    w("## Source Health")
    w("")
    w("| Source | Status | Reference Date | Records | Last Success |")
    w("|--------|--------|----------------|---------|--------------|")
    for source in status["sources"]:
        status_icon = "ok" if source["ok"] else "ERROR"
        last_success = _fmt_dt(source["last_success_at"]) if source["last_success_at"] else "-"
        ref_date = source["last_reference_date"] or "-"
        cnt = f"{source['record_count']:,}"
        w(
            f"| {source['source']} | {status_icon} "
            f"| {ref_date} | {cnt} | {last_success} |"
        )
    w("")

    # Dashboard details
    w("## Dashboard Details")
    w("")
    detail_rows = [
        (
            "Exchange Rates",
            "`data/history/usd_lkr_spot.csv`, `data/history/*_indicative.csv`, "
            "`data/history/*_tt_*.csv`",
            "Tracks spot direction, compares major currencies, and highlights "
            "TT spread differences.",
        ),
        (
            "Inflation",
            "`data/history/ccpi_colombo.csv` and `data/latest/dcs_ccpi.json`",
            "Summarizes the latest CCPI release with MoM, YoY, and moving-average context.",
        ),
        (
            "Commodity Prices",
            "`data/latest/doa_vegetable_prices.json`, "
            "`data/history/doa_vegetable_prices_*.csv`",
            "Shows latest market prices, daily movers, and market-to-market differences "
            "for key vegetables.",
        ),
    ]
    w("| Section | Source Files | Text Summary |")
    w("|---------|--------------|--------------|")
    for section, sources, summary in detail_rows:
        w(f"| {section} | {sources} | {summary} |")
    w("")

    # Data layout
    w("## Data Layout")
    w("")
    w("```text")
    w("data/")
    w("  latest/        Latest snapshot per family (JSON)")
    w("  history/        History CSVs with stable column order")
    w("  normalized/     Canonical JSON Lines snapshots")
    w("  archives/       Timestamped copies of generated data and assets")
    w("  file_history.csv File-level archive manifest with timestamps and hashes")
    w("  status.json     Source health summary")
    w("```")
    w("")

    # Official sources
    w("## Official Sources")
    w("")
    w("- CBSL exchange rates: <https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates>")
    w("- DCS Inflation and Prices: <https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation>")
    w("- DOA vegetable prices: <https://infohub.doa.gov.lk/vegetable-prices/>")
    w("")

    # Footer
    w("---")
    w("")
    w("![MadeWith](https://img.shields.io/badge/made_with-python-blue)")
    w("[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)")
    w("")

    content = "\n".join(lines)
    write_text(output, content)
    archive_output(output, category="reports", timestamp=now)
    return output
