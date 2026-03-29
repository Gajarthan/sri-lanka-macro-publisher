"""Generate POST.txt formatted as a social media thread."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median

from macro_publisher.config import HISTORY_DIR, LATEST_DIR, REPO_ROOT, STATUS_PATH
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


def generate_post(output: Path | None = None) -> Path:
    """Generate POST.txt as a multi-post social media thread."""

    output = output or (REPO_ROOT / "POST.txt")
    now = utc_now()
    date_str = now.strftime("%Y-%m-%d")

    status = _load_json(STATUS_PATH)
    fx_latest = _load_json(LATEST_DIR / "cbsl_fx.json")
    ccpi_latest = _load_json(LATEST_DIR / "dcs_ccpi.json")
    doa_latest = _load_json(LATEST_DIR / "doa_vegetable_prices.json")

    # Extract key data
    fx_spot = next(
        (r for r in fx_latest["records"] if r["indicator_code"] == "usd_lkr_spot"), None
    )
    ccpi_record = ccpi_latest["records"][0] if ccpi_latest["records"] else None

    total_records = sum(s["record_count"] for s in status["sources"])
    sources_ok = sum(1 for s in status["sources"] if s["ok"])

    # Latest vegetable data
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

    # Currency data
    currencies_text = []
    for label, filename in [
        ("USD", "usd_lkr_spot.csv"),
        ("EUR", "eur_lkr_indicative.csv"),
        ("GBP", "gbp_lkr_indicative.csv"),
    ]:
        rows = _read_csv(HISTORY_DIR / filename)
        if rows:
            val = float(rows[-1]["value"])
            currencies_text.append(f"{label}: {val:.2f}")

    # Top movers
    movers: list[tuple[str, float]] = []
    for r in doa_latest_records:
        yesterday = r.get("metadata", {}).get("yesterday_value")
        if yesterday is None:
            continue
        delta = float(r["value"]) - float(yesterday)
        if abs(delta) > 0:
            item = r.get("metadata", {}).get("item", "")
            movers.append((item, delta))
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    unique_movers: list[tuple[str, float]] = []
    seen_items: set[str] = set()
    for item, delta in movers:
        if item not in seen_items:
            unique_movers.append((item, delta))
            seen_items.add(item)

    parts: list[str] = []

    # Post 1: Overview
    post1 = f"Sri Lanka Macro Data Update - {date_str}\n\n"
    post1 += f"{total_records:,} records | {sources_ok}/{len(status['sources'])} sources healthy\n"
    if fx_spot:
        post1 += f"\nUSD/LKR: {float(fx_spot['value']):.3f}"
    if ccpi_record:
        meta = ccpi_record.get("metadata", {})
        post1 += f"\nCCPI: {float(ccpi_record['value']):.1f}"
        if meta.get("year_on_year_percent"):
            post1 += f" (YoY: {meta['year_on_year_percent']}%)"
    if retail_values:
        post1 += f"\nMedian veg retail: {median(retail_values):.0f} LKR/kg"
    parts.append(post1)

    # Post 2: Exchange rates
    if currencies_text:
        post2 = "Exchange Rates (LKR)\n\n"
        post2 += "\n".join(currencies_text)
        ref = fx_spot["reference_date"] if fx_spot else date_str
        post2 += f"\n\nSource: CBSL official rates ({ref})"
        parts.append(post2)

    # Post 3: Inflation
    if ccpi_record:
        meta = ccpi_record.get("metadata", {})
        post3 = f"Inflation Update - {ccpi_record['reference_date']}\n\n"
        post3 += f"CCPI Colombo: {float(ccpi_record['value']):.1f} index points\n"
        if meta.get("month_on_month_percent"):
            post3 += f"MoM: {meta['month_on_month_percent']}%\n"
        if meta.get("year_on_year_percent"):
            post3 += f"YoY: {meta['year_on_year_percent']}%\n"
        if meta.get("twelve_month_moving_average_percent"):
            post3 += f"12M MA: {meta['twelve_month_moving_average_percent']}%\n"
        post3 += "\nSource: DCS official CCPI release"
        parts.append(post3)

    # Post 4: Vegetable prices
    if unique_movers:
        post4 = f"Vegetable Price Movers - {doa_latest_date}\n\n"
        for item, delta in unique_movers[:5]:
            sign = "+" if delta >= 0 else ""
            direction = "up" if delta > 0 else "down"
            post4 += f"{item}: {sign}{delta:.0f} LKR ({direction})\n"
        post4 += "\nSource: DOA market prices"
        parts.append(post4)

    # Post 5: About
    post5 = "Data from official Sri Lankan sources:\n"
    post5 += "- CBSL exchange rates\n"
    post5 += "- DCS Consumer Price Index\n"
    post5 += "- DOA vegetable market prices\n\n"
    post5 += "All data is open, machine-readable, and Git-tracked.\n"
    post5 += "github.com/your-org/sri-lanka-macro-publisher"
    parts.append(post5)

    content = "\n\n---\n\n".join(f"[{i+1}/{len(parts)}]\n{part}" for i, part in enumerate(parts))
    write_text(output, content + "\n")
    archive_output(output, category="reports", timestamp=now)
    return output
