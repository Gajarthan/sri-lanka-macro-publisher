"""Department of Agriculture vegetable price adapter."""

from __future__ import annotations

from decimal import Decimal

from macro_publisher.config import SETTINGS
from macro_publisher.models import Category, Frequency, SourceCode, SourceDataset
from macro_publisher.normalize.canonical import build_record
from macro_publisher.sources.base import SourceAdapter
from macro_publisher.utils.dates import utc_now


class DOAVegetablePricesAdapter(SourceAdapter):
    """Collect DOA market vegetable prices for the supported vegetable list."""

    name = "doa_vegetable_prices"

    ROOT_URL = "https://infohub.doa.gov.lk/vegetable-prices/"
    ITEM_URL = "https://infohub.doa.gov.lk/vegetable-prices-all/?item={item}#vegchart"
    API_URL = "https://infohub.doa.gov.lk/wp-admin/admin-ajax.php"

    def collect(self, client) -> SourceDataset:
        collected_at = utc_now()
        deduped_records = {}
        source_urls = [self.ROOT_URL]
        for item in SETTINGS.doa_supported_items:
            item_url = self.ITEM_URL.format(item=item.replace(" ", "%20"))
            response = client.get(self.API_URL, params={"action": "get_veg_data", "item": item})
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError(f"Unexpected DOA response for item {item!r}")
            source_urls.append(item_url)
            for record in self._build_item_records(item, item_url, payload, collected_at):
                deduped_records[record.logical_key] = record

        return SourceDataset(
            source_name=self.name,
            source=SourceCode.DOA,
            family_code="doa_vegetable_prices",
            family_name="DOA vegetable market prices",
            source_urls=source_urls,
            collected_at=collected_at,
            records=list(deduped_records.values()),
            metadata={
                "note": (
                    "DOA prices are daily market observations for named markets. "
                    "Market scope is preserved on every record."
                ),
            },
        )

    def _build_item_records(self, item: str, source_url: str, rows: list[dict], collected_at):
        records = []
        item_slug = item.lower().replace(" ", "_")
        for row in rows:
            yesterday_values = {
                ("pettah", "wholesale"): row.get("Pettah_Yesterday_Wholesale"),
                ("pettah", "retail"): row.get("Pettah_Yesterday_Retail"),
                ("dambulla", "wholesale"): row.get("Dambulla_Yesterday_Wholesale"),
                ("dambulla", "retail"): row.get("Dambulla_Yesterday_Retail"),
            }
            for field_name, market_scope, price_type, market_slug in (
                ("Pettah_Today_Wholesale", "Pettah market", "wholesale", "pettah"),
                ("Pettah_Today_Retail", "Pettah market", "retail", "pettah"),
                (
                    "Dambulla_Today_Wholesale",
                    "Dambulla Dedicated Economic Centre",
                    "wholesale",
                    "dambulla",
                ),
                (
                    "Dambulla_Today_Retail",
                    "Dambulla Dedicated Economic Centre",
                    "retail",
                    "dambulla",
                ),
            ):
                raw_value = row.get(field_name)
                if raw_value in (None, "", "null"):
                    continue
                unit = row.get("Unit") or "kg"
                records.append(
                    build_record(
                        indicator_code=f"{item_slug}_{price_type}_price_{market_slug}",
                        series_name=f"{item} {price_type.title()} Price - {market_scope}",
                        category=Category.COMMODITY_PRICE,
                        source=SourceCode.DOA,
                        source_url=source_url,
                        value=Decimal(str(raw_value)),
                        unit=f"LKR per {unit}",
                        frequency=Frequency.DAILY,
                        reference_date=row["Date"],
                        collected_at=collected_at,
                        market_scope=market_scope,
                        metadata={
                            "item": item,
                            "price_type": price_type,
                            "unit": unit,
                            "latest_group": "doa_vegetable_prices",
                            "history_file": f"doa_vegetable_prices_{market_slug}",
                            "yesterday_value": yesterday_values[(market_slug, price_type)],
                        },
                    )
                )
        return records
