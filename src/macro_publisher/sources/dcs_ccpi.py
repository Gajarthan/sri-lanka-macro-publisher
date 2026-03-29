"""DCS CCPI adapter."""

from __future__ import annotations

import io
import re
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone

from bs4 import BeautifulSoup
from pypdf import PdfReader

from macro_publisher.models import Category, Frequency, SourceCode, SourceDataset
from macro_publisher.normalize.canonical import build_record
from macro_publisher.sources.base import SourceAdapter
from macro_publisher.utils.dates import utc_now
from macro_publisher.utils.http import get_bytes, get_text


class DCSCCPIAdapter(SourceAdapter):
    """Collect the latest monthly Colombo Consumer Price Index release."""

    name = "dcs_ccpi"

    INDEX_URL = "https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation/MonthlyCCPI"
    MOVEMENTS_PAGE_URL = (
        "https://www.statistics.gov.lk/InflationAndPrices/StaticalInformation/"
        "MonthlyCCPI/Movementsofthe_CCPI"
    )
    SOURCE_TZ = timezone(timedelta(hours=5, minutes=30))

    def collect(self, client) -> SourceDataset:
        collected_at = utc_now()
        index_html = get_text(client, self.INDEX_URL)
        release_code, release_url = self._latest_release(index_html)
        movements_html = get_text(client, self.MOVEMENTS_PAGE_URL)
        pdf_url = self._extract_pdf_url(movements_html)
        pdf_bytes = get_bytes(client, pdf_url)
        pdf_text = self._extract_pdf_text(pdf_bytes)
        latest_entry = self._extract_latest_entry(pdf_text)

        published_at = datetime.combine(
            datetime.strptime(release_code, "%Y%m%d").date(),
            time.min,
            tzinfo=self.SOURCE_TZ,
        )

        record = build_record(
            indicator_code="ccpi_colombo",
            series_name="Colombo Consumer Price Index (CCPI)",
            category=Category.INFLATION,
            source=SourceCode.DCS,
            source_url=pdf_url,
            value=latest_entry["index_value"],
            unit="index points",
            frequency=Frequency.MONTHLY,
            reference_date=latest_entry["reference_date"],
            published_at=published_at,
            collected_at=collected_at,
            market_scope="Colombo district",
            metadata={
                "latest_group": "dcs_ccpi",
                "history_file": "ccpi_colombo",
                "release_code": release_code,
                "release_page": release_url,
                "year_on_year_percent": latest_entry["year_on_year_percent"],
                "month_on_month_percent": latest_entry["month_on_month_percent"],
                "twelve_month_moving_average_percent": latest_entry[
                    "twelve_month_moving_average_percent"
                ],
                "reference_date_convention": "month_end",
            },
        )

        return SourceDataset(
            source_name=self.name,
            source=SourceCode.DCS,
            family_code="dcs_ccpi",
            family_name="DCS Colombo Consumer Price Index",
            source_urls=[self.INDEX_URL, release_url, self.MOVEMENTS_PAGE_URL, pdf_url],
            collected_at=collected_at,
            records=[record],
            metadata={
                "note": (
                    "Latest release timing is inferred from the CCPI release page, while the "
                    "index values are parsed from the official DCS movements PDF linked on the "
                    "same Monthly CCPI section."
                ),
            },
        )

    def _latest_release(self, index_html: str) -> tuple[str, str]:
        soup = BeautifulSoup(index_html, "lxml")
        releases: dict[str, str] = {}
        for link in soup.find_all("a", href=True):
            href = link["href"]
            match = re.search(r"/MonthlyCCPI/(CCPI_(\d{8})E)$", href)
            if match:
                releases[match.group(2)] = self._absolute_url(href)
        if not releases:
            raise ValueError(
                "No English CCPI release links were found on the DCS Monthly CCPI page."
            )
        latest_code = sorted(releases)[-1]
        return latest_code, releases[latest_code]

    def _extract_pdf_url(self, release_html: str) -> str:
        soup = BeautifulSoup(release_html, "lxml")
        iframe = soup.find("iframe")
        if iframe is None or not iframe.get("src"):
            raise ValueError("Could not locate the CCPI PDF iframe on the DCS release page.")
        return self._absolute_url(iframe["src"])

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _extract_latest_entry(self, text: str) -> dict[str, str | date]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        entry_pattern = re.compile(
            r"^(?:(\d{4})\s+)?"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
            r"(-?\d+(?:\.\d+)?)"
            r"(?:\s+(-?\d+(?:\.\d+)?))?"
            r"(?:\s+(-?\d+(?:\.\d+)?))?"
            r"(?:\s+(-?\d+(?:\.\d+)?))?$"
        )
        current_year: int | None = None
        latest: dict[str, str | date] | None = None
        for line in lines:
            match = entry_pattern.match(line)
            if not match:
                continue
            year_text, month_name, index_value, mom, yoy, moving_average = match.groups()
            if year_text:
                current_year = int(year_text)
            if current_year is None:
                continue
            month_number = datetime.strptime(month_name[:3], "%b").month
            latest = {
                "reference_date": datetime(
                    current_year,
                    month_number,
                    monthrange(current_year, month_number)[1],
                ).date(),
                "index_value": index_value,
                "month_on_month_percent": mom,
                "year_on_year_percent": yoy,
                "twelve_month_moving_average_percent": moving_average,
            }
        if latest is None:
            raise ValueError("Could not parse any monthly entries from the DCS CCPI movements PDF.")
        return latest

    def _absolute_url(self, href: str) -> str:
        if href.startswith("http"):
            return href
        return f"https://www.statistics.gov.lk{href}"
