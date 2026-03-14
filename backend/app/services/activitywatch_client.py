"""Minimal ActivityWatch API client for live ingestion."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urljoin

import httpx


class ActivityWatchClient:
    """Fetch buckets and events from a local ActivityWatch server."""

    def __init__(self, base_url: str, timeout_seconds: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds

    def get_buckets(self) -> dict[str, dict]:
        """Return all available buckets keyed by bucket id."""

        url = urljoin(self.base_url, "buckets/")
        response = httpx.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {}

    def get_events(
        self,
        bucket_id: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        """Fetch bucket events between start and end timestamps."""

        url = urljoin(self.base_url, f"buckets/{bucket_id}/events")
        response = httpx.get(
            url,
            params={"start": start.isoformat(), "end": end.isoformat()},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return payload
        return []
