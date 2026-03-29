"""Generate LEADERBOARD.md with summary rankings across all data."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from macro_publisher.config import HISTORY_DIR, LATEST_DIR, REPO_ROOT, STATUS_PATH
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.fs import write_text


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_leaderboard(output: Path | None = None) -> Path:
    """Generate LEADERBOARD.md with data coverage and volatility rankings."""

    output = output or (REPO_ROOT / "LEADERBOARD.md")
    now = utc_now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []
    w = lines.append

    w("# Leaderboard")
    w("")
    w(f"*Generated: {timestamp}*")
    w("")

    # Data coverage stats
    status = _load_json(STATUS_PATH)
    w("## Data Coverage")
    w("")
    w("| Source | Records | Reference Date Range | Frequency |")
    w("|--------|---------|---------------------|-----------|")

    source_info = {
        "cbsl_fx": ("Business daily", "usd_lkr_spot.csv"),
        "dcs_ccpi": ("Monthly", "ccpi_colombo.csv"),
        "doa_vegetable_prices": ("Daily", "doa_vegetable_prices_pettah.csv"),
    }
    for source in status["sources"]:
        freq, csv_file = source_info.get(source["source"], ("Unknown", ""))
        rows = _read_csv(HISTORY_DIR / csv_file) if csv_file else []
        if rows:
            dates = sorted(r["reference_date"] for r in rows)
            date_range = f"{dates[0]} to {dates[-1]}"
        else:
            date_range = "-"
        w(f"| {source['source']} | {source['record_count']:,} | {date_range} | {freq} |")
    w("")

    # Currency rankings - biggest moves
    w("## Currency Rankings (Biggest Moves)")
    w("")
    currency_files = [
        ("USD/LKR", "usd_lkr_spot.csv"),
        ("EUR/LKR", "eur_lkr_indicative.csv"),
        ("GBP/LKR", "gbp_lkr_indicative.csv"),
        ("JPY/LKR", "jpy_lkr_indicative.csv"),
        ("AUD/LKR", "aud_lkr_indicative.csv"),
        ("CNY/LKR", "cny_lkr_indicative.csv"),
    ]

    currency_stats: list[tuple[str, float, float, float, float]] = []
    for label, filename in currency_files:
        rows = _read_csv(HISTORY_DIR / filename)
        if len(rows) < 2:
            continue
        values = [float(r["value"]) for r in rows]
        latest = values[-1]
        first = values[0]
        high = max(values)
        low = min(values)
        total_change = latest - first
        pct_change = (total_change / first) * 100 if first else 0
        volatility = high - low
        currency_stats.append((label, latest, total_change, pct_change, volatility))

    if currency_stats:
        currency_stats.sort(key=lambda x: abs(x[3]), reverse=True)
        w("| # | Currency | Latest | Total Change | % Change | Range |")
        w("|---:|----------|--------|-------------|----------|-------|")
        for i, (label, latest, change, pct, vol) in enumerate(currency_stats, 1):
            sign = "+" if change >= 0 else ""
            w(
                f"| {i} | {label} | {latest:.2f} "
                f"| {sign}{change:.2f} | {sign}{pct:.1f}% | {vol:.2f} |"
            )
        w("")

    # TT spread rankings
    w("## TT Spread Rankings (Buy-Sell Gap)")
    w("")
    tt_pairs = [
        ("USD", "usd_lkr_tt_buy.csv", "usd_lkr_tt_sell.csv"),
        ("EUR", "eur_lkr_tt_buy.csv", "eur_lkr_tt_sell.csv"),
        ("GBP", "gbp_lkr_tt_buy.csv", "gbp_lkr_tt_sell.csv"),
        ("JPY", "jpy_lkr_tt_buy.csv", "jpy_lkr_tt_sell.csv"),
        ("AUD", "aud_lkr_tt_buy.csv", "aud_lkr_tt_sell.csv"),
        ("CNY", "cny_lkr_tt_buy.csv", "cny_lkr_tt_sell.csv"),
    ]

    spread_stats: list[tuple[str, float, float, float]] = []
    for label, buy_file, sell_file in tt_pairs:
        buy_rows = _read_csv(HISTORY_DIR / buy_file)
        sell_rows = _read_csv(HISTORY_DIR / sell_file)
        if not buy_rows or not sell_rows:
            continue
        latest_buy = float(buy_rows[-1]["value"])
        latest_sell = float(sell_rows[-1]["value"])
        spread = latest_sell - latest_buy
        spread_stats.append((label, latest_buy, latest_sell, spread))

    if spread_stats:
        spread_stats.sort(key=lambda x: x[3], reverse=True)
        w("| # | Currency | TT Buy | TT Sell | Spread |")
        w("|---:|----------|--------|---------|--------|")
        for i, (label, buy, sell, spread) in enumerate(spread_stats, 1):
            w(f"| {i} | {label} | {buy:.2f} | {sell:.2f} | {spread:.2f} |")
        w("")

    # Most volatile vegetables
    w("## Most Volatile Vegetables")
    w("")
    doa_latest = _load_json(LATEST_DIR / "doa_vegetable_prices.json")
    doa_latest_date = max(
        (r["reference_date"] for r in doa_latest["records"]), default=""
    )

    veg_volatility: dict[str, list[float]] = defaultdict(list)
    for r in doa_latest["records"]:
        if r["reference_date"] != doa_latest_date:
            continue
        meta = r.get("metadata", {})
        yesterday = meta.get("yesterday_value")
        if yesterday is None:
            continue
        item = meta.get("item", "Unknown")
        delta = abs(float(r["value"]) - float(yesterday))
        veg_volatility[item].append(delta)

    veg_ranked = [
        (item, sum(deltas) / len(deltas), max(deltas))
        for item, deltas in veg_volatility.items()
        if deltas
    ]
    veg_ranked.sort(key=lambda x: x[1], reverse=True)

    if veg_ranked:
        w("| # | Item | Avg Daily Move | Max Daily Move |")
        w("|---:|------|---------------|----------------|")
        for i, (item, avg_delta, max_delta) in enumerate(veg_ranked[:15], 1):
            w(f"| {i} | {item} | {avg_delta:.0f} LKR | {max_delta:.0f} LKR |")
        w("")

    # Highest priced vegetables
    w("## Highest Priced Vegetables (Latest)")
    w("")
    veg_prices: list[tuple[str, str, str, float]] = []
    for r in doa_latest["records"]:
        if r["reference_date"] != doa_latest_date:
            continue
        meta = r.get("metadata", {})
        veg_prices.append((
            meta.get("item", ""),
            r.get("market_scope", ""),
            meta.get("price_type", ""),
            float(r["value"]),
        ))

    veg_prices.sort(key=lambda x: x[3], reverse=True)
    if veg_prices:
        w("| # | Item | Market | Type | Price (LKR/kg) |")
        w("|---:|------|--------|------|----------------|")
        for i, (item, market, ptype, price) in enumerate(veg_prices[:15], 1):
            w(f"| {i} | {item} | {market} | {ptype} | {price:.0f} |")
        w("")

    # Footer
    w("---")
    w("")
    w(f"*Leaderboard generated from full archive through {timestamp}*")
    w("")

    content = "\n".join(lines)
    write_text(output, content)
    return output
