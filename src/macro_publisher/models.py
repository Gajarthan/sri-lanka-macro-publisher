"""Typed models shared by collectors, publishers, and the CLI."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator


class Category(StrEnum):
    """Supported high-level dataset categories."""

    EXCHANGE_RATE = "exchange_rate"
    INFLATION = "inflation"
    COMMODITY_PRICE = "commodity_price"


class Frequency(StrEnum):
    """Canonical frequency values."""

    DAILY = "daily"
    BUSINESS_DAILY = "business_daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SourceCode(StrEnum):
    """Known official sources in the MVP."""

    CBSL = "cbsl"
    DCS = "dcs"
    DOA = "doa"


class CanonicalRecord(BaseModel):
    """Canonical observation schema published by the project."""

    indicator_code: str
    series_name: str
    category: Category
    source: SourceCode
    source_url: str
    value: Decimal
    unit: str
    frequency: Frequency
    reference_date: date
    published_at: datetime | None = None
    collected_at: datetime
    market_scope: str | None = None
    currency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("collected_at", "published_at")
    @classmethod
    def _ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value

    @property
    def logical_key(self) -> tuple[str, str, str, str]:
        """Stable deduplication key for history storage."""

        return (
            self.source,
            self.indicator_code,
            self.reference_date.isoformat(),
            self.market_scope or "",
        )

    def latest_group_key(self) -> str:
        """Return a stable grouping key for latest family outputs."""

        return self.metadata.get("latest_group", self.indicator_code)

    def history_file_stem(self) -> str:
        """Return the history CSV stem for this record."""

        return self.metadata.get("history_file", self.indicator_code)

    @field_serializer("value")
    def _serialize_value(self, value: Decimal) -> float:
        return float(value)


class SourceDataset(BaseModel):
    """A collected and normalized batch from one source adapter."""

    source_name: str
    source: SourceCode
    family_code: str
    family_name: str
    source_urls: list[str]
    collected_at: datetime
    records: list[CanonicalRecord]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("collected_at")
    @classmethod
    def _ensure_dataset_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("dataset timestamps must be timezone-aware")
        return value


class SourceStatus(BaseModel):
    """Status information persisted to ``data/status.json``."""

    source: str
    ok: bool
    last_attempt_at: datetime
    last_success_at: datetime | None = None
    last_reference_date: date | None = None
    record_count: int = 0
    error: str | None = None
    content_hash: str | None = None

    @field_validator("last_attempt_at", "last_success_at")
    @classmethod
    def _ensure_status_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("status timestamps must be timezone-aware")
        return value
