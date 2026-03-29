from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont

from macro_publisher.utils.archive import archive_output
from macro_publisher.utils.dates import utc_now

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "docs" / "readme-assets"
RUN_AT = utc_now()

WIDTH = 1440
PANEL_PADDING = 36
CARD_GAP = 20

COLORS = {
    "bg": "#f4ecdf",
    "panel": "#fffaf3",
    "card": "#fffdf8",
    "border": "#e7dac6",
    "ink": "#1e2a38",
    "muted": "#687689",
    "grid": "#dbcbb8",
    "orange": "#d97b2c",
    "teal": "#237f83",
    "red": "#c14c38",
    "gold": "#caa03a",
    "green": "#31764a",
    "blue": "#2b5f9e",
    "purple": "#6d50b8",
}

FONT_PATHS = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("C:/Windows/Fonts/georgiab.ttf"),
    Path("C:/Windows/Fonts/georgia.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
]


@dataclass(frozen=True)
class Series:
    label: str
    values: list[float]
    color: str


def find_font(preferred: list[Path], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in preferred:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_SERIF_LG = find_font(FONT_PATHS[:2], 52)
FONT_SERIF_MD = find_font(FONT_PATHS[:2], 30)
FONT_SERIF_SM = find_font(FONT_PATHS[:2], 22)
FONT_SANS_MD = find_font(FONT_PATHS[2:], 18)
FONT_SANS_SM = find_font(FONT_PATHS[2:], 15)
FONT_SANS_XS = find_font(FONT_PATHS[2:], 13)
FONT_SANS_LG = find_font(FONT_PATHS[2:], 34)


def save_image(image: Image.Image, name: str) -> None:
    path = OUT_DIR / name
    image.save(path)
    archive_output(path, category="charts", timestamp=RUN_AT)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_metadata(row: dict[str, str]) -> dict[str, str]:
    return json.loads(row["metadata"])


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = COLORS["border"],
    radius: int = 24,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    font: ImageFont.ImageFont,
    fill: str = COLORS["ink"],
    anchor: str | None = None,
) -> None:
    draw.text(xy, value, font=font, fill=fill, anchor=anchor)


def panel_base(
    title: str, subtitle: str, section: str, chips: list[str], height: int
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, height), COLORS["bg"])
    draw = ImageDraw.Draw(image)
    rounded_rectangle(draw, (18, 18, WIDTH - 18, height - 18), COLORS["panel"], radius=34)
    text(draw, (54, 54), section.upper(), FONT_SANS_XS, COLORS["orange"])
    text(draw, (54, 84), title, FONT_SERIF_LG)
    text(draw, (56, 152), subtitle, FONT_SANS_MD, COLORS["muted"])

    chip_x = WIDTH - 56
    for chip in reversed(chips):
        bbox = draw.textbbox((0, 0), chip, font=FONT_SANS_SM)
        chip_w = bbox[2] - bbox[0] + 30
        chip_box = (chip_x - chip_w, 46, chip_x, 78)
        rounded_rectangle(draw, chip_box, "#efe8df", radius=18)
        text(draw, (chip_box[0] + 15, chip_box[1] + 8), chip, FONT_SANS_SM)
        chip_x = chip_box[0] - 12
    return image, draw


def card_metric(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    kicker: str,
    value: str,
    note: str,
) -> None:
    rounded_rectangle(draw, box, COLORS["card"])
    text(draw, (box[0] + 22, box[1] + 18), kicker.upper(), FONT_SANS_XS, COLORS["muted"])
    text(draw, (box[0] + 22, box[1] + 54), value, FONT_SERIF_MD)
    text(draw, (box[0] + 22, box[1] + 108), note, FONT_SANS_SM, COLORS["muted"])


def draw_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title_value: str,
    series: list[Series],
    labels: list[str],
    suffix: str,
) -> None:
    rounded_rectangle(draw, box, COLORS["card"])
    left, top, right, bottom = box
    text(draw, (left + 20, top + 18), title_value, FONT_SERIF_SM)

    legend_x = right - 18
    for item in reversed(series):
        bbox = draw.textbbox((0, 0), item.label, font=FONT_SANS_SM)
        label_w = bbox[2] - bbox[0]
        legend_x -= label_w + 26
        draw.ellipse((legend_x, top + 24, legend_x + 10, top + 34), fill=item.color)
        text(draw, (legend_x + 16, top + 18), item.label, FONT_SANS_SM, COLORS["muted"])
        legend_x -= 18

    chart_left = left + 26
    chart_top = top + 74
    chart_right = right - 24
    chart_bottom = bottom - 78

    for index in range(4):
        y = chart_top + (chart_bottom - chart_top) * index / 3
        draw.line((chart_left, y, chart_right, y), fill=COLORS["grid"], width=1)

    values = [value for item in series for value in item.values]
    low = min(values)
    high = max(values)
    if low == high:
        low -= 1
        high += 1

    for item in series:
        points: list[tuple[float, float]] = []
        span = max(1, len(item.values) - 1)
        for idx, value in enumerate(item.values):
            x = chart_left + (chart_right - chart_left) * idx / span
            ratio = (value - low) / (high - low)
            y = chart_bottom - ratio * (chart_bottom - chart_top)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=item.color, width=5, joint="curve")

    if labels:
        tick_positions = [
            (labels[0], chart_left),
            (labels[len(labels) // 2], (chart_left + chart_right) // 2),
            (labels[-1], chart_right),
        ]
        for label, x in tick_positions:
            text(
                draw, (int(x), chart_bottom + 12), label, FONT_SANS_XS, COLORS["muted"], anchor="ma"
            )

    pill_x = left + 20
    pill_y = bottom - 48
    for item in series:
        value_text = f"{item.label} {item.values[-1]:,.1f}{suffix}"
        bbox = draw.textbbox((0, 0), value_text, font=FONT_SANS_XS)
        pill_w = bbox[2] - bbox[0] + 24
        rounded_rectangle(
            draw, (pill_x, pill_y, pill_x + pill_w, pill_y + 32), "#f1ece4", radius=16
        )
        text(draw, (pill_x + 12, pill_y + 8), value_text, FONT_SANS_XS, COLORS["muted"])
        pill_x += pill_w + 10


def draw_table(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title_value: str,
    headers: list[str],
    rows: list[list[str]],
) -> None:
    rounded_rectangle(draw, box, COLORS["card"])
    left, top, right, bottom = box
    text(draw, (left + 20, top + 18), title_value, FONT_SERIF_SM)

    col_width = (right - left - 40) // len(headers)
    y = top + 62
    for idx, header in enumerate(headers):
        text(draw, (left + 20 + idx * col_width, y), header.upper(), FONT_SANS_XS, COLORS["muted"])
    y += 30
    draw.line((left + 20, y, right - 20, y), fill=COLORS["border"], width=2)

    row_height = 42
    for row in rows:
        y += 16
        for idx, cell in enumerate(row):
            text(draw, (left + 20 + idx * col_width, y), cell, FONT_SANS_SM)
        y += row_height - 16
        draw.line((left + 20, y, right - 20, y), fill=COLORS["border"], width=1)


def draw_heatmap(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title_value: str,
    row_labels: list[str],
    col_labels: list[str],
    matrix: list[list[float]],
) -> None:
    rounded_rectangle(draw, box, COLORS["card"])
    left, top, right, bottom = box
    text(draw, (left + 20, top + 18), title_value, FONT_SERIF_SM)
    text(draw, (right - 150, top + 22), "Lower to higher price", FONT_SANS_XS, COLORS["muted"])

    values = [value for row in matrix for value in row]
    low = min(values)
    high = max(values)
    if low == high:
        high = low + 1

    def color_for(value: float) -> str:
        ratio = (value - low) / (high - low)
        if ratio < 0.33:
            return "#f4dbbf"
        if ratio < 0.66:
            return "#e7a463"
        return "#bb5b2d"

    grid_left = left + 150
    grid_top = top + 62
    grid_right = right - 18
    grid_bottom = bottom - 40
    cell_w = (grid_right - grid_left) / len(col_labels)
    cell_h = (grid_bottom - grid_top) / len(row_labels)

    for row_idx, label in enumerate(row_labels):
        text(
            draw,
            (left + 18, int(grid_top + row_idx * cell_h + 10)),
            label,
            FONT_SANS_XS,
            COLORS["muted"],
        )
        for col_idx, value in enumerate(matrix[row_idx]):
            x0 = int(grid_left + col_idx * cell_w)
            y0 = int(grid_top + row_idx * cell_h)
            x1 = int(grid_left + (col_idx + 1) * cell_w - 4)
            y1 = int(grid_top + (row_idx + 1) * cell_h - 4)
            draw.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=color_for(value))

    for col_idx, label in enumerate(col_labels):
        x = int(grid_left + col_idx * cell_w + cell_w / 2)
        text(draw, (x, bottom - 26), label, FONT_SANS_XS, COLORS["muted"], anchor="ma")


def build_overview() -> None:
    status = load_json(DATA_DIR / "status.json")
    fx_latest = load_json(DATA_DIR / "latest" / "cbsl_fx.json")
    ccpi_latest = load_json(DATA_DIR / "latest" / "dcs_ccpi.json")
    doa_latest = load_json(DATA_DIR / "latest" / "doa_vegetable_prices.json")

    fx_record = next(
        record for record in fx_latest["records"] if record["indicator_code"] == "usd_lkr_spot"
    )
    ccpi_record = ccpi_latest["records"][0]
    veg_latest_date = max(record["reference_date"] for record in doa_latest["records"])
    veg_latest = [
        record for record in doa_latest["records"] if record["reference_date"] == veg_latest_date
    ]
    retail_values = [
        float(record["value"])
        for record in veg_latest
        if record["metadata"].get("price_type") == "retail"
    ]

    image, draw = panel_base(
        "Overview",
        "Latest stats, freshness, quick links, and source health from the published files.",
        "Section 1",
        ["static-first", "GitHub Pages ready", "official sources"],
        700,
    )

    left_col = 48
    top_cards = 190
    card_w = 360
    card_h = 128
    metrics = [
        ("USD/LKR spot", f"{float(fx_record['value']):.3f}", "Latest CBSL business-day spot"),
        (
            "CCPI Colombo",
            f"{float(ccpi_record['value']):.1f}",
            f"Reference {ccpi_record['reference_date']}",
        ),
        (
            "Median veg retail",
            f"{median(retail_values):.0f}",
            f"Across {len(retail_values)} latest DOA series",
        ),
        (
            "Source health",
            "All green" if all(source["ok"] for source in status["sources"]) else "Review",
            "From data/status.json",
        ),
    ]
    for idx, metric in enumerate(metrics):
        row = idx // 2
        col = idx % 2
        x = left_col + col * (card_w + CARD_GAP)
        y = top_cards + row * (card_h + 18)
        card_metric(draw, (x, y, x + card_w, y + card_h), *metric)

    box = (808, 190, 1388, 454)
    rounded_rectangle(draw, box, COLORS["card"])
    text(draw, (box[0] + 22, box[1] + 18), "Freshness and quick links", FONT_SERIF_MD)
    text(
        draw,
        (box[0] + 22, box[1] + 66),
        f"FX latest: {fx_record['reference_date']}",
        FONT_SANS_MD,
        COLORS["muted"],
    )
    text(
        draw,
        (box[0] + 22, box[1] + 102),
        f"CCPI latest: {ccpi_record['reference_date']}",
        FONT_SANS_MD,
        COLORS["muted"],
    )
    text(
        draw,
        (box[0] + 22, box[1] + 138),
        f"Vegetables latest: {veg_latest_date}",
        FONT_SANS_MD,
        COLORS["muted"],
    )
    links = ["CBSL exchange rates", "DCS Monthly CCPI", "DOA vegetable prices"]
    for idx, link in enumerate(links):
        text(draw, (box[0] + 22, box[1] + 188 + idx * 30), link, FONT_SANS_MD, COLORS["blue"])

    rows = [
        [
            source["source"],
            "ok" if source["ok"] else "error",
            source["last_reference_date"] or "-",
            str(source["record_count"]),
            parse_dt(source["last_success_at"]).strftime("%Y-%m-%d %H:%M UTC")
            if source["last_success_at"]
            else "-",
        ]
        for source in status["sources"]
    ]
    draw_table(
        draw,
        (48, 478, 1388, 652),
        "Source freshness / health panel",
        ["Source", "Status", "Reference date", "Records", "Last success"],
        rows,
    )
    save_image(image, "overview-dashboard.png")


def build_exchange_rates() -> None:
    image, draw = panel_base(
        "Exchange Rates",
        "USD/LKR trend, major-currency comparison, and TT spreads using CBSL business-day history.",
        "Section 2",
        ["spot", "indicative", "TT buy/sell"],
        990,
    )
    spot_rows = read_csv_rows(DATA_DIR / "history" / "usd_lkr_spot.csv")[-10:]
    indicative_rows = read_csv_rows(DATA_DIR / "history" / "usd_lkr_indicative.csv")[-10:]
    labels = [row["reference_date"][5:] for row in spot_rows]
    draw_chart(
        draw,
        (48, 192, 700, 560),
        "USD/LKR trend line",
        [
            Series("Spot", [float(row["value"]) for row in spot_rows], COLORS["orange"]),
            Series("Indicative", [float(row["value"]) for row in indicative_rows], COLORS["teal"]),
        ],
        labels,
        " LKR",
    )

    indexed_series: list[Series] = []
    for label, filename, color in [
        ("USD", "usd_lkr_indicative.csv", COLORS["orange"]),
        ("EUR", "eur_lkr_indicative.csv", COLORS["blue"]),
        ("GBP", "gbp_lkr_indicative.csv", COLORS["green"]),
        ("JPY", "jpy_lkr_indicative.csv", COLORS["red"]),
        ("AUD", "aud_lkr_indicative.csv", COLORS["gold"]),
        ("CNY", "cny_lkr_indicative.csv", COLORS["purple"]),
    ]:
        rows = read_csv_rows(DATA_DIR / "history" / filename)[-10:]
        values = [float(row["value"]) for row in rows]
        base = values[0]
        indexed_series.append(Series(label, [value / base * 100 for value in values], color))
    draw_chart(
        draw,
        (720, 192, 1388, 560),
        "Multi-currency comparison chart",
        indexed_series,
        labels,
        " index",
    )

    spread_series: list[Series] = []
    for label, buy_file, sell_file, color in [
        ("USD", "usd_lkr_tt_buy.csv", "usd_lkr_tt_sell.csv", COLORS["orange"]),
        ("EUR", "eur_lkr_tt_buy.csv", "eur_lkr_tt_sell.csv", COLORS["blue"]),
        ("GBP", "gbp_lkr_tt_buy.csv", "gbp_lkr_tt_sell.csv", COLORS["green"]),
        ("JPY", "jpy_lkr_tt_buy.csv", "jpy_lkr_tt_sell.csv", COLORS["red"]),
    ]:
        buy_rows = read_csv_rows(DATA_DIR / "history" / buy_file)[-10:]
        sell_rows = read_csv_rows(DATA_DIR / "history" / sell_file)[-10:]
        spreads = [
            float(sell["value"]) - float(buy["value"])
            for buy, sell in zip(buy_rows, sell_rows, strict=True)
        ]
        spread_series.append(Series(label, spreads, color))
    draw_chart(
        draw,
        (48, 584, 1388, 930),
        "TT buy vs sell spread",
        spread_series,
        labels,
        " LKR",
    )
    save_image(image, "exchange-rates-dashboard.png")


def build_inflation() -> None:
    ccpi_rows = read_csv_rows(DATA_DIR / "history" / "ccpi_colombo.csv")
    row = ccpi_rows[-1]
    metadata = parse_metadata(row)
    image, draw = panel_base(
        "Inflation",
        "Monthly CCPI line chart plus the headline change cards from the latest official release.",
        "Section 3",
        ["monthly", "CCPI Colombo"],
        650,
    )
    draw_chart(
        draw,
        (48, 192, 780, 590),
        "CCPI level chart",
        [Series("CCPI", [float(item["value"]) for item in ccpi_rows], COLORS["red"])],
        [item["reference_date"][:7] for item in ccpi_rows],
        " pts",
    )

    metrics = [
        ("Latest CCPI", f"{float(row['value']):.1f}", "Index points"),
        ("Month-on-month", f"{metadata['month_on_month_percent']}%", "Latest official movement"),
        ("Year-on-year", f"{metadata['year_on_year_percent']}%", "Annual change"),
        (
            "12-month moving average",
            f"{metadata['twelve_month_moving_average_percent']}%",
            "Trend smoothing",
        ),
    ]
    x0 = 808
    y0 = 192
    for idx, metric in enumerate(metrics):
        row_idx = idx // 2
        col_idx = idx % 2
        x = x0 + col_idx * (280 + 18)
        y = y0 + row_idx * (142 + 16)
        card_metric(draw, (x, y, x + 280, y + 142), *metric)

    rounded_rectangle(draw, (808, 510, 1388, 590), COLORS["card"])
    text(draw, (830, 528), "Release note", FONT_SERIF_SM)
    note = (
        "This preview uses the current repository history. As more monthly snapshots "
        "are collected, the CCPI line chart grows automatically."
    )
    text(draw, (830, 570), note, FONT_SANS_SM, COLORS["muted"])
    save_image(image, "inflation-dashboard.png")


def build_commodities() -> None:
    image, draw = panel_base(
        "Commodity Prices",
        "Market comparison, item filters, heatmaps, and top daily movers from the "
        "DOA commodity family.",
        "Section 4",
        ["Pettah", "Dambulla", "wholesale", "retail"],
        980,
    )
    pettah_rows = read_csv_rows(DATA_DIR / "history" / "doa_vegetable_prices_pettah.csv")
    dambulla_rows = read_csv_rows(DATA_DIR / "history" / "doa_vegetable_prices_dambulla.csv")
    items = [
        "Beans",
        "Carrot",
        "Cabbage",
        "Tomato",
        "Brinjal",
        "Snake Gourd",
        "Pumpkin",
        "Green Chilli",
    ]
    dates = sorted({row["reference_date"] for row in pettah_rows})[-10:]

    matrix: list[list[float]] = []
    for item in items:
        row_values: list[float] = []
        for date in dates:
            matches = [
                entry
                for entry in pettah_rows
                if entry["reference_date"] == date
                and parse_metadata(entry)["item"] == item
                and parse_metadata(entry)["price_type"] == "wholesale"
            ]
            row_values.append(float(matches[-1]["value"]) if matches else 0.0)
        matrix.append(row_values)
    draw_heatmap(
        draw,
        (48, 192, 700, 600),
        "Vegetable price heatmap",
        items,
        [date[5:] for date in dates],
        matrix,
    )

    compare_item = "Beans"
    pettah_series = [
        float(entry["value"])
        for entry in pettah_rows
        if parse_metadata(entry)["item"] == compare_item
        and parse_metadata(entry)["price_type"] == "wholesale"
        and entry["reference_date"] in dates
    ]
    dambulla_series = [
        float(entry["value"])
        for entry in dambulla_rows
        if parse_metadata(entry)["item"] == compare_item
        and parse_metadata(entry)["price_type"] == "wholesale"
        and entry["reference_date"] in dates
    ]
    draw_chart(
        draw,
        (720, 192, 1388, 600),
        "Market comparison chart",
        [
            Series("Pettah wholesale", pettah_series, COLORS["green"]),
            Series("Dambulla wholesale", dambulla_series, COLORS["orange"]),
        ],
        [date[5:] for date in dates],
        " LKR",
    )

    latest_family = load_json(DATA_DIR / "latest" / "doa_vegetable_prices.json")
    latest_date = max(record["reference_date"] for record in latest_family["records"])
    movers: list[tuple[str, str, str]] = []
    for record in latest_family["records"]:
        if record["reference_date"] != latest_date:
            continue
        yesterday = record["metadata"].get("yesterday_value")
        if yesterday is None:
            continue
        delta = float(record["value"]) - float(yesterday)
        movers.append((record["series_name"], f"{float(record['value']):.0f}", f"{delta:+.0f}"))
    movers_sorted = (
        sorted(movers, key=lambda item: float(item[2]), reverse=True)[:4]
        + sorted(movers, key=lambda item: float(item[2]))[:4]
    )
    draw_table(
        draw,
        (48, 624, 1388, 920),
        "Top movers table",
        ["Series", "Latest value", "Daily move"],
        [list(row) for row in movers_sorted],
    )
    save_image(image, "commodity-prices-dashboard.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_overview()
    build_exchange_rates()
    build_inflation()
    build_commodities()
    print(f"Wrote dashboard previews to {OUT_DIR}")


if __name__ == "__main__":
    main()
