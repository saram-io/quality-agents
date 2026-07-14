"""Mock database containing CSV Standard Operating Procedures (SOPs) and audit logging utility."""

import logging
from typing import Dict, List, Optional

# Configure module-level logging
logger = logging.getLogger("app.database")


class SOPDatabase:
    """Mock database of Standard Operating Procedures (SOPs)."""

    def __init__(self) -> None:
        self._sops: Dict[str, str] = {
            "SOP-101": (
                "SOP-101: Software Validation Standard. "
                "Any software deployed in a GxP environment requires a User Requirement Specification (URS). "
                "For GAMP 5 Category 4 systems, Functional Specifications (FS) and IQ/OQ testing are required. "
                "For Category 5 custom systems, a full validation lifecycle (URS, FS, DS, IQ/OQ/PQ) is mandatory."
            ),
            "SOP-202": (
                "SOP-202: Electronic Records and Signatures (21 CFR Part 11). "
                "Systems must maintain a secure, computer-generated, time-stamped audit trail "
                "recording the date, time, and operator action for any modifications. "
                "Electronic signatures must be unique to one individual and display the printed name, "
                "date/time of execution, and the meaning of the signature."
            ),
            "SOP-303": (
                "SOP-303: Quality Risk Management. "
                "A formal risk assessment is required to identify GxP impact, determine validation scope, "
                "and define mitigations for critical-to-quality functions."
            )
        }

    def get_sop_section(self, sop_id: str) -> str:
        """Fetch raw string section of an SOP by its unique ID.

        Args:
            sop_id: Unique identifier for the SOP.

        Returns:
            The raw text content of the SOP, or an error message if not found.
        """
        content = self._sops.get(sop_id)
        if not content:
            return f"Error: SOP {sop_id} not found in the quality database."
        return content

    def search_sops(self, keyword: str) -> List[str]:
        """Search SOP database for matching keyword terms."""
        keyword_lower = keyword.lower()
        return [
            content for content in self._sops.values()
            if keyword_lower in content.lower()
        ]

    def get_all_documents(self) -> List[Dict[str, str]]:
        """Format and return all SOP documents for semantic vector database indexing."""
        docs = []
        for sop_id, content in self._sops.items():
            parts = content.split(":", 1)
            title = ""
            if len(parts) > 1:
                title_parts = parts[1].split(".", 1)
                title = title_parts[0].strip()
            
            docs.append({
                "sop_id": sop_id,
                "section_title": title or f"SOP {sop_id} Details",
                "content": content
            })
        return docs


class AuditLogger:
    """Utility to record execution traces and compliance checkpoints."""

    def __init__(self) -> None:
        self.logs: List[Dict[str, str]] = []

    def log_step(self, step_name: str, message: str) -> None:
        """Write execution steps cleanly to logger and internal logs.

        Args:
            step_name: The name/phase of the execution step.
            message: Detail or status of the step.
        """
        log_entry = {"step": step_name, "message": message}
        self.logs.append(log_entry)
        logger.info(f"[{step_name}] {message}")
        print(f"AUDIT TRAIL: [{step_name}] {message}")
