"""Generate matplotlib chart PNGs from published history data."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.dates import utc_now

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
LATEST_DIR = DATA_DIR / "latest"
OUT_DIR = REPO_ROOT / "docs" / "readme-assets"
RUN_AT = utc_now()

DARK_BG = "#0f1117"
PANEL_BG = "#1a1d2e"
GRID_COLOR = "#2a2d3e"
TEXT_COLOR = "#e0e0e0"
MUTED = "#7a7f8e"
ACCENT_COLORS = ["#f59e0b", "#06b6d4", "#10b981", "#ef4444", "#a78bfa", "#ec4899"]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _style_ax(ax: plt.Axes, title: str) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.5)


def _save(fig: plt.Figure, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    archive_output(path, category="charts", timestamp=RUN_AT)
    print(f"  {path}")


def build_fx_trend() -> None:
    """USD/LKR spot and indicative trend line."""
    spot = _read_csv(HISTORY_DIR / "usd_lkr_spot.csv")
    indic = _read_csv(HISTORY_DIR / "usd_lkr_indicative.csv")
    if not spot:
        return

    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=DARK_BG)
    _style_ax(ax, "USD/LKR Exchange Rate")

    dates = [_parse_date(r["reference_date"]) for r in spot]
    vals = [float(r["value"]) for r in spot]
    ax.plot(dates, vals, color=ACCENT_COLORS[0], linewidth=2.5, label="Spot")

    if indic:
        d2 = [_parse_date(r["reference_date"]) for r in indic]
        v2 = [float(r["value"]) for r in indic]
        ax.plot(d2, v2, color=ACCENT_COLORS[1], linewidth=2, label="Indicative",
                linestyle="--", alpha=0.8)

    low = min(vals) - 1
    ax.fill_between(dates, vals, low, alpha=0.15, color=ACCENT_COLORS[0])
    ax.set_ylim(low, max(vals) + 1)
    ax.set_ylabel("LKR per USD", color=MUTED, fontsize=10)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR,
              fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate(rotation=30)
    _save(fig, "fx_trend.png")


def build_multi_currency() -> None:
    """Multi-currency indexed comparison chart."""
    pairs = [
        ("USD", "usd_lkr_indicative.csv"),
        ("EUR", "eur_lkr_indicative.csv"),
        ("GBP", "gbp_lkr_indicative.csv"),
        ("JPY", "jpy_lkr_indicative.csv"),
        ("AUD", "aud_lkr_indicative.csv"),
        ("CNY", "cny_lkr_indicative.csv"),
    ]

    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=DARK_BG)
    _style_ax(ax, "Major Currencies vs LKR (Indexed to 100)")

    for idx, (label, filename) in enumerate(pairs):
        rows = _read_csv(HISTORY_DIR / filename)
        if len(rows) < 2:
            continue
        dates = [_parse_date(r["reference_date"]) for r in rows]
        vals = [float(r["value"]) for r in rows]
        base = vals[0]
        indexed = [v / base * 100 for v in vals]
        ax.plot(dates, indexed, color=ACCENT_COLORS[idx % len(ACCENT_COLORS)],
                linewidth=2, label=label)

    ax.axhline(y=100, color=MUTED, linewidth=0.8, linestyle=":")
    ax.set_ylabel("Index (base = 100)", color=MUTED, fontsize=10)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR,
              fontsize=8, ncol=3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate(rotation=30)
    _save(fig, "multi_currency.png")


def build_tt_spreads() -> None:
    """TT buy vs sell spread bars."""
    pairs = [
        ("USD", "usd_lkr_tt_buy.csv", "usd_lkr_tt_sell.csv"),
        ("EUR", "eur_lkr_tt_buy.csv", "eur_lkr_tt_sell.csv"),
        ("GBP", "gbp_lkr_tt_buy.csv", "gbp_lkr_tt_sell.csv"),
        ("AUD", "aud_lkr_tt_buy.csv", "aud_lkr_tt_sell.csv"),
        ("CNY", "cny_lkr_tt_buy.csv", "cny_lkr_tt_sell.csv"),
    ]

    labels, buys, sells, spreads = [], [], [], []
    for label, buy_f, sell_f in pairs:
        buy_rows = _read_csv(HISTORY_DIR / buy_f)
        sell_rows = _read_csv(HISTORY_DIR / sell_f)
        if not buy_rows or not sell_rows:
            continue
        b = float(buy_rows[-1]["value"])
        s = float(sell_rows[-1]["value"])
        labels.append(label)
        buys.append(b)
        sells.append(s)
        spreads.append(s - b)

    if not labels:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=DARK_BG,
                                    gridspec_kw={"width_ratios": [2, 1]})

    _style_ax(ax1, "TT Buy vs Sell Rates")
    x = range(len(labels))
    bar_w = 0.35
    ax1.bar([i - bar_w / 2 for i in x], buys, bar_w, label="TT Buy",
            color=ACCENT_COLORS[1], alpha=0.85)
    ax1.bar([i + bar_w / 2 for i in x], sells, bar_w, label="TT Sell",
            color=ACCENT_COLORS[0], alpha=0.85)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("LKR", color=MUTED, fontsize=10)
    ax1.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR,
               fontsize=9)

    _style_ax(ax2, "Spread (Sell - Buy)")
    colors = [ACCENT_COLORS[3] if s > 10 else ACCENT_COLORS[2] for s in spreads]
    ax2.barh(labels, spreads, color=colors, alpha=0.85)
    ax2.set_xlabel("LKR", color=MUTED, fontsize=10)
    for i, v in enumerate(spreads):
        ax2.text(v + 0.2, i, f"{v:.1f}", va="center", color=TEXT_COLOR, fontsize=9)

    fig.tight_layout(pad=2)
    _save(fig, "tt_spreads.png")


def build_inflation() -> None:
    """CCPI level chart with annotations."""
    rows = _read_csv(HISTORY_DIR / "ccpi_colombo.csv")
    if not rows:
        return

    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=DARK_BG)
    _style_ax(ax, "Colombo Consumer Price Index (CCPI)")

    dates = [_parse_date(r["reference_date"]) for r in rows]
    vals = [float(r["value"]) for r in rows]
    ax.plot(dates, vals, color=ACCENT_COLORS[3], linewidth=2.5, marker="o",
            markersize=6)
    ax.fill_between(dates, vals, alpha=0.15, color=ACCENT_COLORS[3])

    last = rows[-1]
    meta = json.loads(last["metadata"])
    note = (
        f"Latest: {float(last['value']):.1f}  |  "
        f"MoM: {meta.get('month_on_month_percent', '?')}%  |  "
        f"YoY: {meta.get('year_on_year_percent', '?')}%"
    )
    ax.annotate(note, xy=(0.5, -0.18), xycoords="axes fraction",
                ha="center", fontsize=9, color=MUTED)
    ax.set_ylabel("Index points", color=MUTED, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=30)
    _save(fig, "inflation_trend.png")


def build_vegetable_heatmap() -> None:
    """Vegetable price heatmap for Pettah wholesale."""
    rows = _read_csv(HISTORY_DIR / "doa_vegetable_prices_pettah.csv")
    if not rows:
        return

    items_set = set()
    dates_set = set()
    price_map: dict[tuple[str, str], float] = {}

    for r in rows:
        meta = json.loads(r["metadata"])
        if meta.get("price_type") != "wholesale":
            continue
        item = meta.get("item", "")
        date = r["reference_date"]
        items_set.add(item)
        dates_set.add(date)
        price_map[(item, date)] = float(r["value"])

    items = sorted(items_set)
    dates = sorted(dates_set)[-15:]

    if not items or not dates:
        return

    matrix = []
    for item in items:
        row = [price_map.get((item, d), 0) for d in dates]
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(12, 5), facecolor=DARK_BG)
    ax.set_facecolor(PANEL_BG)

    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(items, fontsize=9, color=TEXT_COLOR)
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels([d[5:] for d in dates], fontsize=8, color=MUTED, rotation=45,
                        ha="right")
    ax.set_title("Pettah Wholesale Prices (LKR/kg)", color=TEXT_COLOR,
                 fontsize=14, fontweight="bold", pad=12)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.ax.tick_params(colors=MUTED, labelsize=8)
    cbar.set_label("LKR/kg", color=MUTED, fontsize=9)

    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
    ax.tick_params(colors=MUTED)

    fig.tight_layout(pad=2)
    _save(fig, "vegetable_heatmap.png")


def build_market_comparison() -> None:
    """Pettah vs Dambulla wholesale price comparison."""
    pettah = _read_csv(HISTORY_DIR / "doa_vegetable_prices_pettah.csv")
    dambulla = _read_csv(HISTORY_DIR / "doa_vegetable_prices_dambulla.csv")
    if not pettah or not dambulla:
        return

    items = ["Beans", "Carrot", "Cabbage", "Tomato", "Brinjal",
             "Green Chilli", "Pumpkin", "Snake Gourd"]

    def _latest_prices(
        rows: list[dict[str, str]],
    ) -> dict[str, float]:
        latest_date = max(r["reference_date"] for r in rows)
        prices: dict[str, float] = {}
        for r in rows:
            if r["reference_date"] != latest_date:
                continue
            meta = json.loads(r["metadata"])
            if meta.get("price_type") != "wholesale":
                continue
            prices[meta.get("item", "")] = float(r["value"])
        return prices

    p_prices = _latest_prices(pettah)
    d_prices = _latest_prices(dambulla)

    valid_items = [i for i in items if i in p_prices and i in d_prices]
    if not valid_items:
        return

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=DARK_BG)
    _style_ax(ax, "Market Comparison: Pettah vs Dambulla (Wholesale)")

    x = range(len(valid_items))
    bar_w = 0.35
    p_vals = [p_prices[i] for i in valid_items]
    d_vals = [d_prices[i] for i in valid_items]

    ax.bar([i - bar_w / 2 for i in x], p_vals, bar_w, label="Pettah",
           color=ACCENT_COLORS[2], alpha=0.85)
    ax.bar([i + bar_w / 2 for i in x], d_vals, bar_w, label="Dambulla",
           color=ACCENT_COLORS[0], alpha=0.85)

    ax.set_xticks(list(x))
    ax.set_xticklabels(valid_items, rotation=30, ha="right")
    ax.set_ylabel("LKR/kg", color=MUTED, fontsize=10)
    ax.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR,
              fontsize=9)

    fig.tight_layout(pad=2)
    _save(fig, "market_comparison.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating matplotlib charts...")
    build_fx_trend()
    build_multi_currency()
    build_tt_spreads()
    build_inflation()
    build_vegetable_heatmap()
    build_market_comparison()
    print("Done.")


if __name__ == "__main__":
    main()
