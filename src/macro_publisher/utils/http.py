"""HTTP helpers used by source adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

import httpx

from macro_publisher.config import SETTINGS


def build_http_client() -> httpx.Client:
    """Create a shared HTTP client with a stable user agent."""

    return httpx.Client(
        follow_redirects=True,
        headers={"User-Agent": SETTINGS.user_agent},
        timeout=SETTINGS.http_timeout_seconds,
    )


def get_text(client: httpx.Client, url: str, **kwargs: Any) -> str:
    """Fetch a text response and raise on HTTP failures."""

    response = client.get(url, **kwargs)
    response.raise_for_status()
    return response.text


def get_bytes(client: httpx.Client, url: str, **kwargs: Any) -> bytes:
    """Fetch raw bytes and raise on HTTP failures."""

    response = client.get(url, **kwargs)
    response.raise_for_status()
    return response.content


def post_form(
    client: httpx.Client,
    url: str,
    data: Mapping[str, Any] | list[tuple[str, Any]],
    **kwargs: Any,
) -> str:
    """POST form data and return the response body as text."""

    encoded = urlencode(data, doseq=True)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = client.post(url, content=encoded, headers=headers, **kwargs)
    response.raise_for_status()
    return response.text
