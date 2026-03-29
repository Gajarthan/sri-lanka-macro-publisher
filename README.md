# sri-lanka-macro-publisher

`sri-lanka-macro-publisher` is a static-data publishing pipeline for official Sri Lankan macroeconomic datasets.

It fetches data from official public sources, normalizes observations into a canonical schema, validates records, writes machine-readable JSON and CSV outputs into Git-tracked files, and keeps source health metadata in `data/status.json`.

This repository is intentionally static-first.

- It does not expose an API service yet.
- It does not use a database for the MVP.
- It does not treat official business-day or daily datasets as realtime streaming feeds.

## Why This Is Not Realtime

The MVP sources are official publication systems with business-day, daily, or monthly release cadences:

- CBSL exchange rates are official business-day exchange-rate publications.
- DCS CCPI is a monthly official inflation release.
- DOA vegetable prices are daily market observations for named markets.

The project preserves those source realities. If a source is business-day or monthly, the canonical records say so through `frequency`, `reference_date`, and source metadata.

## Official Sources

- CBSL exchange rates: <https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates>
- DCS Inflation and Prices: <https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation>
- DCS Monthly CCPI: <https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation/MonthlyCCPI>
- DCS advance release calendar: <https://www.statistics.gov.lk/qlink/ADRCalender>
- DOA vegetable prices: <https://infohub.doa.gov.lk/vegetable-prices/>

## Supported MVP Datasets

- `cbsl_fx`
  - USD/LKR spot indicative rate
  - major indicative exchange rates when available
  - TT buy and sell rates for supported currencies when available
- `dcs_ccpi`
  - Colombo Consumer Price Index (CCPI)
- `doa_vegetable_prices`
  - daily market prices for supported vegetables
  - market scope preserved for Pettah and Dambulla
  - wholesale and retail price series preserved separately

## Canonical Schema

Every published observation is normalized into the canonical record shape below:

```json
{
  "indicator_code": "usd_lkr_spot",
  "series_name": "USD/LKR Spot Indicative Exchange Rate",
  "category": "exchange_rate",
  "source": "cbsl",
  "source_url": "https://www.cbsl.gov.lk/...",
  "value": 314.22,
  "unit": "LKR per USD",
  "frequency": "business_daily",
  "reference_date": "2026-03-27",
  "published_at": null,
  "collected_at": "2026-03-29T08:00:00Z",
  "market_scope": "Sri Lanka interbank",
  "currency": "USD",
  "metadata": {}
}
```

Notes:

- `reference_date` is the date the observation refers to.
- `published_at` is included when the official source exposes a usable release date.
- `collected_at` is when this pipeline fetched the data.
- `market_scope` is used for localized market datasets such as DOA prices.
- monthly series use month-end as `reference_date` in the MVP, and that convention is called out in metadata.

## Data Layout

```text
data/
├── latest/
├── history/
├── normalized/
└── status.json
```

- `data/latest/*.json`
  - latest snapshot per family, for example `cbsl_fx.json`
- `data/history/*.csv`
  - history CSVs with stable column order
  - exchange-rate and CCPI series are stored per logical series
  - DOA history is grouped by market family, for example `doa_vegetable_prices_dambulla.csv`
- `data/normalized/*.jsonl`
  - canonical JSON Lines snapshots per family
- `data/status.json`
  - source health summary and last successful collection metadata

## Revision and Deduplication Policy

History CSVs are append-mostly.

- New logical keys are appended.
- Duplicate logical keys are not appended again.
- If a source republishes a changed value for the same logical key, the existing row is replaced in place instead of duplicating the day.

This keeps `latest/` authoritative and keeps `history/` deterministic for Git diffs.

## Local Setup

Requirements:

- Python 3.12
- `uv` for dependency and environment management

Install:

```bash
uv sync --all-extras --dev
```

## Running the Pipeline

Run everything:

```bash
uv run python -m macro_publisher.cli run-all
```

Run one source:

```bash
uv run python -m macro_publisher.cli run-source cbsl_fx
uv run python -m macro_publisher.cli run-source dcs_ccpi
uv run python -m macro_publisher.cli run-source doa_vegetable_prices
```

Run a source smoke test without writing outputs:

```bash
uv run python -m macro_publisher.cli healthcheck
```

## GitHub Actions

- `ci.yml`
  - runs on `push` and `pull_request`
  - installs dependencies
  - runs lint and tests
- `pipeline.yml`
  - scheduled publishing automation
  - CBSL FX every 3 hours on weekdays
  - DOA daily
  - DCS CCPI daily
  - commits changed `data/` files back to the repository
- `source-health.yml`
  - weekly smoke test
  - validates source structure and parser health without publishing data

## Static Publishing and GitHub Pages

The repository is designed so the `data/` directory can be published directly as static artifacts.

Typical options:

- serve the repository with GitHub Pages
- consume `data/latest/*.json` from the repository raw URLs
- mirror `data/` into another static host or CDN later

Because the project writes plain JSON, CSV, and JSONL files, no application server is required for read-only publishing.

## Extending the Project

To add a new source family:

1. Add a new adapter under `src/macro_publisher/sources/`.
2. Normalize records with `build_record()` in `normalize/canonical.py`.
3. Register the adapter in `src/macro_publisher/sources/__init__.py`.
4. Add fixture-backed parser tests under `tests/`.
5. Decide the history grouping strategy through `metadata["history_file"]` when needed.
6. Update the README and workflows if the new source needs a new cadence.

Keep new adapters:

- typed
- deterministic
- based on official sources only
- explicit about source assumptions

## Parser Assumptions to Review

These are the main source-structure assumptions in the MVP:

- CBSL
  - public exchange-rate pages embed official iframe forms
  - the iframe form POST targets remain stable:
    - `cbsl_custom/exrates/exrates_results_spot_mid.php`
    - `cbsl_custom/exrates/exrates_results.php`
    - `cbsl_custom/exratestt/exrates_resultstt.php`
  - result pages continue to render one `h2` heading followed by a result table per selected currency
- DCS
  - the Monthly CCPI index page continues to publish English release links in the `CCPI_YYYYMMDDE` form
  - the official movements PDF remains linked from `Movementsofthe_CCPI`
  - the movements PDF continues to extract text as a simple year/month table with index and inflation columns
- DOA
  - the public item pages continue to use the official AJAX endpoint
    - `wp-admin/admin-ajax.php?action=get_veg_data&item=...`
  - response field names remain:
    - `Pettah_Today_Wholesale`
    - `Pettah_Today_Retail`
    - `Dambulla_Today_Wholesale`
    - `Dambulla_Today_Retail`

If any of those structures change, `healthcheck` and CI smoke tests should fail loudly.

## Limitations and Caveats

- No OCR is used in the MVP.
- No live websocket or streaming support exists.
- No raw HTML or PDF archives are committed to Git by default.
- DOA item coverage is limited to the supported list configured in `config.py`.
- `published_at` may be unknown for some daily datasets and is left `null` in those cases.

## Compliance Note

This project republishes official public statistics and official public market/exchange-rate data with source attribution. It is a convenience publishing layer, not a replacement for the original agencies. For legal, policy, or interpretation questions, always refer back to the original source publications.
