"""
Base Ingestion Adapter
Abstract base class for all external and public dataset ingestion adapters.
Provides rate limiting, exponential backoff, timeout handling, and provenance tracking.
"""
from abc import ABC, abstractmethod
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ....schemas.knowledge import (
    KnowledgeEntity,
    KnowledgeSource,
    FieldProvenance,
    VerificationStatusEnum,
    PriceStatusEnum,
    utc_now_iso,
)


class BaseIngestionAdapter(ABC):
    def __init__(
        self,
        source: KnowledgeSource,
        request_timeout_seconds: float = 8.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.source = source
        self.timeout = request_timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._last_request_time = 0.0
        self._min_interval = 60.0 / max(source.rate_limit_per_minute, 1)

    def _apply_rate_limit(self):
        """Enforces inter-request interval to respect rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _http_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Executes HTTP GET with rate limiting, timeouts, and exponential backoff."""
        req_headers = {"User-Agent": "VoyantraKnowledgeEngine/2.0 (tourism-research)"}
        if headers:
            req_headers.update(headers)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            self._apply_rate_limit()
            try:
                resp = requests.get(url, params=params, headers=req_headers, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp
                if resp.status_code in [429, 500, 502, 503, 504]:
                    time.sleep(self.backoff_factor * attempt)
                    continue
                resp.raise_for_status()
            except Exception as exc:
                last_error = exc
                time.sleep(self.backoff_factor * attempt)

        raise RuntimeError(f"HTTP request to {url} failed after {self.max_retries} attempts: {last_error}")

    @abstractmethod
    def fetch_raw_records(self, city_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches raw records from the data source for a given city."""
        pass

    @abstractmethod
    def transform_to_entity(self, raw_record: Dict[str, Any], city_id: str) -> KnowledgeEntity:
        """Transforms a raw external record into a standardized KnowledgeEntity."""
        pass

    def create_field_provenance(self, source_url: Optional[str] = None, confidence: float = 0.9) -> FieldProvenance:
        """Helper to create standardized field-level provenance."""
        return FieldProvenance(
            source_id=self.source.id,
            source_url=source_url or self.source.base_url,
            license=self.source.license_name,
            retrieved_at=utc_now_iso(),
            confidence=confidence,
        )
