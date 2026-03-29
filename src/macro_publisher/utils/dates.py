"""Date and time helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def utc_now() -> datetime:
    """Return the current UTC time with timezone information."""

    return datetime.now(UTC)


def days_ago(days: int) -> date:
    """Return the UTC date ``days`` ago."""

    return utc_now().date() - timedelta(days=days)


def iso_date(value: date | None) -> str | None:
    """Serialize a date to ISO-8601."""

    return value.isoformat() if value else None


def iso_datetime(value: datetime | None) -> str | None:
    """Serialize a timezone-aware datetime to ISO-8601."""

    return value.isoformat() if value else None


def parse_iso_date(value: str) -> date:
    """Parse an ISO-8601 date string."""

    return date.fromisoformat(value)
