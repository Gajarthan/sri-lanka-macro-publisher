"""Base interfaces for source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from macro_publisher.models import SourceDataset


class SourceAdapter(ABC):
    """Abstract base class for source collectors."""

    name: str

    @abstractmethod
    def collect(self, client: httpx.Client) -> SourceDataset:
        """Collect, normalize, and return records from a source."""

    def healthcheck(self, client: httpx.Client) -> SourceDataset:
        """Run a source check using the standard collection path."""

        return self.collect(client)
