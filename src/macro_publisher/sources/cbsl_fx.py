"""CBSL exchange-rate adapter."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup

from macro_publisher.config import SETTINGS
from macro_publisher.models import Category, Frequency, SourceCode, SourceDataset
from macro_publisher.normalize.canonical import build_record
from macro_publisher.sources.base import SourceAdapter
from macro_publisher.utils.dates import days_ago, utc_now
from macro_publisher.utils.http import post_form


class CBSLFXAdapter(SourceAdapter):
    """Collect CBSL spot, indicative, and TT buy/sell exchange rates."""

    name = "cbsl_fx"

    SPOT_PAGE_URL = (
        "https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates/"
        "daily-indicative-usd-spot-exchange-rates"
    )
    SPOT_RESULTS_URL = "https://www.cbsl.gov.lk/cbsl_custom/exrates/exrates_results_spot_mid.php"

    INDICATIVE_PAGE_URL = (
        "https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates/daily-indicative-exchange-rates"
    )
    INDICATIVE_RESULTS_URL = "https://www.cbsl.gov.lk/cbsl_custom/exrates/exrates_results.php"

    TT_PAGE_URL = (
        "https://www.cbsl.gov.lk/en/rates-and-indicators/exchange-rates/"
        "daily-buy-and-sell-exchange-rates"
    )
    TT_RESULTS_URL = "https://www.cbsl.gov.lk/cbsl_custom/exratestt/exrates_resultstt.php"

    INDICATIVE_CURRENCIES = {
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "Sterling Pound",
        "JPY": "Japanese Yen",
        "CNY": "Chinese Yuan (Renminbi)",
        "AUD": "Australian Dollar",
    }
    TT_CURRENCIES = {
        "USD": "United States Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "JPY": "Yen",
        "CNY": "Renminbi",
        "AUD": "Australian Dollar",
    }

    def collect(self, client) -> SourceDataset:
        collected_at = utc_now()
        start_date = days_ago(SETTINGS.history_lookback_days)
        end_date = collected_at.date()

        records = []
        records.extend(self._collect_spot(client, start_date, end_date, collected_at))
        records.extend(self._collect_indicative(client, start_date, end_date, collected_at))
        records.extend(self._collect_tt(client, start_date, end_date, collected_at))

        return SourceDataset(
            source_name=self.name,
            source=SourceCode.CBSL,
            family_code="cbsl_fx",
            family_name="CBSL exchange rates",
            source_urls=[self.SPOT_PAGE_URL, self.INDICATIVE_PAGE_URL, self.TT_PAGE_URL],
            collected_at=collected_at,
            records=records,
            metadata={
                "lookback_days": SETTINGS.history_lookback_days,
                "note": "CBSL exchange rates are business-day official rates, not realtime ticks.",
            },
        )

    def _collect_spot(self, client, start_date: date, end_date: date, collected_at):
        html = self._post_result(
            client=client,
            url=self.SPOT_RESULTS_URL,
            selected=["USD~US Dollar"],
            start_date=start_date,
            end_date=end_date,
        )
        rows = self._parse_tables(html).get("US Dollar", [])
        records = []
        for row_date, lkr_rate, inverse_rate in rows:
            records.append(
                build_record(
                    indicator_code="usd_lkr_spot",
                    series_name="USD/LKR Spot Indicative Exchange Rate",
                    category=Category.EXCHANGE_RATE,
                    source=SourceCode.CBSL,
                    source_url=self.SPOT_PAGE_URL,
                    value=lkr_rate,
                    unit="LKR per USD",
                    frequency=Frequency.BUSINESS_DAILY,
                    reference_date=row_date,
                    collected_at=collected_at,
                    market_scope="Sri Lanka interbank",
                    currency="USD",
                    metadata={
                        "inverse_rate": str(inverse_rate),
                        "latest_group": "cbsl_fx",
                        "rate_type": "spot_indicative",
                    },
                )
            )
        return records

    def _collect_indicative(self, client, start_date: date, end_date: date, collected_at):
        html = self._post_result(
            client=client,
            url=self.INDICATIVE_RESULTS_URL,
            selected=[f"{code}~{label}" for code, label in self.INDICATIVE_CURRENCIES.items()],
            start_date=start_date,
            end_date=end_date,
        )
        parsed = self._parse_tables(html)
        records = []
        for code, label in self.INDICATIVE_CURRENCIES.items():
            for row_date, lkr_rate, inverse_rate in parsed.get(label, []):
                records.append(
                    build_record(
                        indicator_code=f"{code.lower()}_lkr_indicative",
                        series_name=f"{code}/LKR Indicative Exchange Rate",
                        category=Category.EXCHANGE_RATE,
                        source=SourceCode.CBSL,
                        source_url=self.INDICATIVE_PAGE_URL,
                        value=lkr_rate,
                        unit=f"LKR per {code}",
                        frequency=Frequency.BUSINESS_DAILY,
                        reference_date=row_date,
                        collected_at=collected_at,
                        currency=code,
                        metadata={
                            "inverse_rate": str(inverse_rate),
                            "latest_group": "cbsl_fx",
                            "rate_type": "indicative",
                        },
                    )
                )
        return records

    def _collect_tt(self, client, start_date: date, end_date: date, collected_at):
        html = self._post_result(
            client=client,
            url=self.TT_RESULTS_URL,
            selected=[f"{code}~{label}" for code, label in self.TT_CURRENCIES.items()],
            start_date=start_date,
            end_date=end_date,
        )
        parsed = self._parse_tt_tables(html)
        records = []
        for code, label in self.TT_CURRENCIES.items():
            for row_date, buy_rate, sell_rate in parsed.get(label, []):
                common = {
                    "category": Category.EXCHANGE_RATE,
                    "source": SourceCode.CBSL,
                    "source_url": self.TT_PAGE_URL,
                    "frequency": Frequency.BUSINESS_DAILY,
                    "reference_date": row_date,
                    "collected_at": collected_at,
                    "currency": code,
                    "market_scope": "Sri Lanka licensed bank TT average at 9:30 AM",
                    "metadata": {
                        "latest_group": "cbsl_fx",
                        "rate_family": "telegraphic_transfer",
                    },
                }
                records.append(
                    build_record(
                        indicator_code=f"{code.lower()}_lkr_tt_buy",
                        series_name=f"{code}/LKR TT Buy Exchange Rate",
                        value=buy_rate,
                        unit=f"LKR per {code}",
                        **common,
                    )
                )
                records.append(
                    build_record(
                        indicator_code=f"{code.lower()}_lkr_tt_sell",
                        series_name=f"{code}/LKR TT Sell Exchange Rate",
                        value=sell_rate,
                        unit=f"LKR per {code}",
                        **common,
                    )
                )
        return records

    def _post_result(
        self,
        *,
        client,
        url: str,
        selected: list[str],
        start_date: date,
        end_date: date,
    ) -> str:
        payload: list[tuple[str, str]] = [
            ("lookupPage", "lookup_daily_exchange_rates.php"),
            ("startRange", "2006-11-11"),
            ("rangeType", "dates"),
            ("txtStart", start_date.isoformat()),
            ("txtEnd", end_date.isoformat()),
            ("submit_button", "Submit"),
        ]
        payload.extend(("chk_cur[]", item) for item in selected)
        return post_form(client, url, payload)

    def _parse_tables(self, html: str) -> dict[str, list[tuple[date, Decimal, Decimal]]]:
        soup = BeautifulSoup(html, "lxml")
        parsed: dict[str, list[tuple[date, Decimal, Decimal]]] = {}
        for heading in soup.find_all("h2"):
            heading_text = heading.get_text(" ", strip=True)
            table = heading.find_next("table")
            if table is None or "0 results" in table.get_text(" ", strip=True):
                parsed[heading_text] = []
                continue
            rows: list[tuple[date, Decimal, Decimal]] = []
            for row in table.select("tbody tr"):
                cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
                if len(cells) != 3:
                    continue
                rows.append((date.fromisoformat(cells[0]), Decimal(cells[1]), Decimal(cells[2])))
            parsed[heading_text] = rows
        return parsed

    def _parse_tt_tables(self, html: str) -> dict[str, list[tuple[date, Decimal, Decimal]]]:
        return self._parse_tables(html)
