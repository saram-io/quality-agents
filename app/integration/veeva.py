"""Specialized GxP Veeva Vault Electronic Document Management System (EDMS) connector."""

import os
import uuid
import logging
from typing import Dict, Any
from app.integration.connectors import BaseEnterpriseConnector

logger = logging.getLogger("app.integration.veeva")


class VeevaVaultConnector(BaseEnterpriseConnector):
    """GxP-compliant Veeva Vault EDMS interface."""

    def __init__(self, base_url: str = None) -> None:
        url = base_url or os.getenv("VEEVA_VAULT_URL", "https://mock-veeva.gxp-vault.com/api/v1")
        super().__init__(url)
        # Enable sandbox mock mode if explicitly requested or default keys are not present
        self.mock_mode = os.getenv("CSV_INTEGRATION_MOCK", "True").lower() == "true"
        self.username = os.getenv("VEEVA_VAULT_USERNAME", "mock_user")
        self.password = os.getenv("VEEVA_VAULT_PASSWORD", "mock_pass")

    async def _authenticate(self) -> str:
        """Acquires a session token from Veeva Vault API."""
        if self.mock_mode:
            return "mock-session-token-abc123xyz"

        url = f"{self.base_url}/auth"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"username": self.username, "password": self.password}
        
        self._log_request("POST", url, headers, "username=***, password=***")
        
        response = await self.client.post(url, data=data, timeout=10.0)
        response.raise_for_status()
        res_data = response.json()
        
        # In Veeva Vault REST API, authentication returns session token in vaulthits
        session_id = res_data.get("vaulthits", {}).get("session_id")
        if not session_id:
            # Alternate parsing under standard API versions
            session_id = res_data.get("session_id")
        if not session_id:
            raise ValueError("Authentication response does not contain a session_id.")
        return session_id

    async def fetch_source_change_record(self, ticket_id: str, tenant_id: str) -> Dict[str, Any]:
        """Retrieves change logs or requirement definitions from Veeva Vault Object Framework.

        Args:
            ticket_id: Veeva Vault Change Control document reference ID.
            tenant_id: Scope separation identifier.
        """
        if self.mock_mode:
            logger.info(f"VEEVA_MOCK: Fetching Change Control metadata for '{ticket_id}' under tenant '{tenant_id}'.")
            return {
                "ticket_id": ticket_id,
                "title": f"Regulatory Change control ticket - {ticket_id}",
                "description": "Auto-sync: Requires PostgreSQL database with secure transaction logging.",
                "status": "Approved",
                "gamp_category": 5
            }

        session_id = await self._authenticate()
        url = f"{self.base_url}/objects/change_controls/{ticket_id}"
        headers = {
            "Authorization": f"Bearer {session_id}",
            "X-Vault-Tenant": tenant_id
        }
        
        self._log_request("GET", url, headers)
        response = await self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def upload_approved_document(
        self,
        document_payload: bytes,
        metadata: Dict[str, Any],
        tenant_id: str
    ) -> str:
        """Uploads the signed validation deliverable and binds custom metadata attributes.

        Args:
            document_payload: Locked compiled bytes payload (PDF or Markdown text).
            metadata: Contains key validation run parameters and electronic signature tokens.
            tenant_id: Scope separation identifier.
        """
        # Formulate Veeva-specific custom field names
        gamp_class = f"Category {metadata.get('gamp_category', 0)}"
        audit_hash = metadata.get("audit_hash", "UNKNOWN_HASH")
        status_value = "Pending Approval" if not metadata.get("approved", True) else "Approved"

        if self.mock_mode:
            logger.info(
                f"VEEVA_MOCK: Uploading signed document under tenant '{tenant_id}'. "
                f"Classification: {gamp_class}, Audit Chained Hash: {audit_hash}, Status: {status_value}."
            )
            # Generate remote document ID
            remote_doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
            return remote_doc_id

        session_id = await self._authenticate()
        url = f"{self.base_url}/documents"
        headers = {
            "Authorization": f"Bearer {session_id}",
            "X-Vault-Tenant": tenant_id
        }
        
        # Veeva REST API accepts form multipart/form-data for document uploads
        files = {
            "file": ("validation_package.pdf", document_payload, "application/pdf")
        }
        data = {
            "name__v": f"Validation_Protocol_{metadata.get('doc_id', 'UNSPECIFIED')}",
            "type__v": "Validation Document",
            "GAMP_Classification__c": gamp_class,
            "AI_Audit_Chain_Hash__c": audit_hash,
            "status__v": status_value
        }
        
        self._log_request("POST", url, headers, data)
        response = await self.client.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()
        res_data = response.json()
        
        remote_id = res_data.get("id")
        if not remote_id:
            raise ValueError("Veeva Vault response missing remote document identifier.")
        return str(remote_id)
