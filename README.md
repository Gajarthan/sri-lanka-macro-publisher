# Sri Lanka Macro Publisher

Static-data publishing pipeline for official Sri Lankan macroeconomic datasets.
It fetches official public releases, normalizes observations into a canonical
schema, validates records, and publishes machine-readable JSON and CSV outputs.

The dashboard block below is auto-generated from published files under `data/`.
Refresh it locally with `python scripts/generate_readme_dashboard.py`.

<!-- BEGIN: DASHBOARD -->
## Published Data Dashboard

_Auto-generated from published data files. Do not edit inside this block manually._

**Pipeline last updated (UTC):** 2026-03-29 09:24:31 UTC  
**Total published records:** 29,915

### Latest Snapshot

| Metric | Latest value | Source reference date |
|--------|--------------|-----------------------|
| USD/LKR Spot | 314.386 | 2026-03-27 |
| CCPI Colombo | 195.3 | 2026-02-28 |
| Median vegetable retail | 160 LKR/kg | 2026-03-27 |

### Inflation Summary

| Measure | Value |
|---------|-------|
| CCPI level | 195.3 |
| Month-on-month | -0.9% |
| Year-on-year | 1.6% |
| 12-month moving average | 0.5% |
| Source publication date | 2026-02-27 00:00:00 +0530 |
| Source reference month | 2026-02-28 |

### Source Health

| Source | Status | Pipeline updated at (UTC) | Source reference date | Records |
|--------|--------|---------------------------|-----------------------|---------|
| cbsl_fx | ok | 2026-03-29 09:24:21 UTC | 2026-03-27 | 190 |
| dcs_ccpi | ok | 2026-03-29 09:24:24 UTC | 2026-02-28 | 1 |
| doa_vegetable_prices | ok | 2026-03-29 09:24:31 UTC | 2026-03-27 | 29,724 |

### Exchange Rates Sample

| Date | USD/LKR spot |
|------|--------------|
| 2026-03-27 | 314.386 |
| 2026-03-26 | 313.509 |
| 2026-03-25 | 314.217 |
| 2026-03-24 | 312.964 |
| 2026-03-23 | 311.747 |

### Vegetable Prices Sample

_Source reference date: 2026-03-27_

| Item | Market | Price type | LKR/kg |
|------|--------|------------|--------|
| Beans | Pettah | wholesale | 300 |
| Brinjal | Pettah | wholesale | 120 |
| Cabbage | Pettah | wholesale | 100 |
| Carrot | Pettah | wholesale | 300 |
| Green Chilli | Pettah | wholesale | 250 |
| Lime | Pettah | wholesale | 100 |
| Pumpkin | Pettah | wholesale | 140 |
| Snake Gourd | Pettah | wholesale | 130 |

### Dashboard-to-File Mapping

| Dashboard section | Published file inputs |
|-------------------|-----------------------|
| Latest snapshot | `data/latest/cbsl_fx.json`, `data/latest/dcs_ccpi.json`, `data/latest/doa_vegetable_prices.json` |
| Source health | `data/status.json` |
| Exchange rates sample | `data/history/usd_lkr_spot.csv` |
| Vegetable prices sample | `data/latest/doa_vegetable_prices.json` and `data/history/doa_vegetable_prices_pettah.csv` |

### Freshness and Cadence

| Source | Source publication cadence | Pipeline check cadence | Freshness note |
|--------|----------------------------|------------------------|----------------|
| cbsl_fx | Business-day official FX rates from CBSL | Every 3 hours on weekdays | Reference date may lag the pipeline update timestamp. |
| dcs_ccpi | Monthly DCS CCPI release | Daily at 02:30 UTC | Reference date may lag the pipeline update timestamp. |
| doa_vegetable_prices | Daily DOA market prices | Daily at 01:15 UTC | Reference date may lag the pipeline update timestamp. |

Pipeline last updated is the most recent successful collection time in the published status files.
Source reference date is the economic observation date, which is distinct from pipeline execution time.
<!-- END: DASHBOARD -->

## Local Command

```bash
python scripts/generate_readme_dashboard.py
```

## Data Layout

```text
data/
  latest/           Latest snapshot per family (JSON)
  history/          History CSVs with stable column order
  normalized/       Canonical JSON Lines snapshots
  archives/         Timestamped copies of generated data and assets
  file_history.csv  File-level archive manifest with timestamps and hashes
  status.json       Source health summary
```

## Official Sources

- CBSL exchange rates: <https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates>
- DCS Inflation and Prices:
  <https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation>
- DOA vegetable prices: <https://infohub.doa.gov.lk/vegetable-prices/>

---

![MadeWith](https://img.shields.io/badge/made_with-python-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
