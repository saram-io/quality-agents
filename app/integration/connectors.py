"""Abstract base classes and rate-limited HTTP client helpers for GxP enterprise integrations."""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
import httpx

logger = logging.getLogger("app.integration")


class BaseEnterpriseConnector(ABC):
    """Abstract connector defining contract interface for pulling and pushing GxP systems metadata."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        # Rate-limited HTTP client with timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    def _scrub_log_string(self, log_str: str) -> str:
        """Utility scrubbing sensitive authorization tokens or credentials from log strings."""
        # Scrub authorization header contents (e.g. Bearer tokens or Session Keys)
        scrubbed = re.sub(
            r"(?i)(Authorization|apiKey|token|session-id|password|client_secret)\s*:\s*[^\s,\'\"]+",
            r"\1: [REDACTED]",
            log_str
        )
        return scrubbed

    def _log_request(self, method: str, url: str, headers: Dict[str, str], payload: Any = None) -> None:
        """Cleanly logs outgoing external HTTP requests with credential scrubbing."""
        header_str = ", ".join(f"{k}={v}" for k, v in headers.items())
        scrubbed_headers = self._scrub_log_string(header_str)
        log_msg = f"INTEGRATION_REQUEST: Outgoing {method} to {url}. Headers: [{scrubbed_headers}]."
        if payload:
            log_msg += f" Payload: {payload}"
        logger.info(self._scrub_log_string(log_msg))

    @abstractmethod
    async def fetch_source_change_record(self, ticket_id: str, tenant_id: str) -> Dict[str, Any]:
        """Retrieves user requirement definitions or change logs from ticketing system (e.g., Jira, ServiceNow)."""
        pass

    @abstractmethod
    async def upload_approved_document(
        self,
        document_payload: bytes,
        metadata: Dict[str, Any],
        tenant_id: str
    ) -> str:
        """Pushes signed validation protocol packs to document management repository (e.g., Veeva Vault)."""
        pass

    async def close(self) -> None:
        """Closes the underlying HTTP client session connection pools."""
        await self.client.aclose()
