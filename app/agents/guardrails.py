"""Real-Time Guardrail Middleware and Compliance Enforcement filters for GxP validation."""

import re
from typing import Set

from app.schemas import QualitySystemDeps, ValidationDraft


class ComplianceViolationException(Exception):
    """Custom exception raised when a critical GxP prompt or data guardrail is violated."""
    pass


class QualityGuardrailManager:
    """Validator registry checking system safety boundaries on prompt inputs and outputs."""

    @staticmethod
    def validate_input_safety(prompt: str) -> None:
        """Scans input prompts to prevent prompt injection overrides and review bypass attempts."""
        prompt_lower = prompt.lower()
        blocked_keywords = [
            "ignore previous instructions",
            "ignore instructions",
            "bypass human review",
            "bypass approval",
            "bypass check",
            "ignore compliance",
            "bypass electronic signature",
            "ignore gamp",
        ]

        for word in blocked_keywords:
            if word in prompt_lower:
                raise ComplianceViolationException(
                    f"Prompt Safety Violation: Detected request attempting to '{word}'."
                )

    @staticmethod
    def validate_draft_residency_and_citations(deps: QualitySystemDeps, draft: ValidationDraft) -> None:
        """Enforces data residency rules and checks for citation hallucinations in generated drafts.

        Args:
            deps: Shared QualitySystemDeps injected context.
            draft: The structured ValidationDraft object to validate.
        """
        # 1. Data Residency Check: scan for external domains / hostnames
        # Standard GxP systems must not refer to external hosting endpoints (e.g., s3.amazonaws.com, external-api.com)
        external_url_pattern = re.compile(
            r"https?://(?!localhost|127\.0\.0\.1|[\w\-]+\.local)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}"
        )
        
        for section_title, content in draft.sections.items():
            if external_url_pattern.search(content) or "s3.amazonaws.com" in content.lower():
                raise ValueError(
                    f"Data Residency Violation: Section '{section_title}' references unauthorized "
                    "external cloud storage or foreign server hostnames."
                )

        # 2. SOP Cross-Reference Alignment: verify cited SOPs exist in the quality db
        # Scan for cited SOPs matching the pattern SOP-<number>
        sop_pattern = re.compile(r"\bSOP-\d+\b")
        cited_sops: Set[str] = set()
        
        for content in draft.sections.values():
            for match in sop_pattern.findall(content):
                cited_sops.add(match)
        
        # Check against db
        for sop_id in cited_sops:
            if not deps.sop_db.get_sop_section(sop_id) or "not found" in deps.sop_db.get_sop_section(sop_id).lower():
                raise ValueError(
                    f"SOP Citation Hallucination: Cited SOP '{sop_id}' does not exist in the "
                    "regulatory compliance database."
                )
