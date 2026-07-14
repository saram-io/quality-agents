"""Pydantic validation schemas and dependency types for the CSV system."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .database import SOPDatabase, AuditLogger
from .vector_store import QualityVectorStoreManager
from .auth.tenant import UserSession


@dataclass
class QualitySystemDeps:
    """Dependency container injected into the multi-agent system."""
    current_user: str
    target_system: str
    sop_db: SOPDatabase
    audit_logger: AuditLogger
    vector_store: QualityVectorStoreManager
    gamp_category: Optional[int] = None
    job_id: Optional[str] = None
    session: Optional[UserSession] = None
    event_broker: Optional[Any] = None


class GroundingAnalysis(BaseModel):
    """Regulatory grounding mapping requirements to standards and SOPs."""
    applicable_sops: List[str] = Field(
        description="IDs of Standard Operating Procedures (SOPs) or clauses that apply to the system requirements."
    )
    regulatory_constraints: List[str] = Field(
        description="Specific constraints from 21 CFR Part 11 or GAMP guidelines (e.g., audit trails, electronic signature rules)."
    )
    gamp_category: int = Field(
        description="Identified software GAMP category (e.g., 1 for Infrastructure, 3 for Non-Configured, 4 for Configured, 5 for Custom)."
    )
    retrieved_chunks: List[str] = Field(
        description="Raw contextual text chunks extracted from the vector database."
    )
    confidence_scores: List[float] = Field(
        description="Vector similarity metrics / confidence scores associated with each matched chunk."
    )


class ValidationDraft(BaseModel):
    """Validation deliverable document drafted by the system."""
    document_type: str = Field(
        description="Type of CSV document being drafted (e.g., URS, FS, IQ, OQ, PQ)."
    )
    sections: Dict[str, str] = Field(
        description="Dictionary of document sections mapped to their Markdown content (e.g., {'Purpose': '...', 'Scope': '...'})."
    )
    verification_checklist: List[str] = Field(
        description="List of verification checklist items that must be completed/executed."
    )
    is_draft: bool = Field(
        default=True,
        description="Compliance status flag. Documents must remain marked as drafts until signed off."
    )


class ReviewReport(BaseModel):
    """Quality and regulatory review report outcome."""
    approved: bool = Field(
        description="Whether the document is approved. True only if all compliance checks pass."
    )
    validation_gaps: List[str] = Field(
        description="List of regulatory gaps, missing requirements, or quality issues identified."
    )
    remedial_actions_required: Optional[str] = Field(
        default=None,
        description="Required remediation steps needed to address validation gaps and gain approval."
    )


class SignaturePayload(BaseModel):
    """Electronic signature metadata complying with 21 CFR Part 11."""
    signer: str = Field(description="Printed name or email of the electronic signer")
    timestamp: str = Field(description="Date and time of execution in ISO format")
    meaning: str = Field(description="Legal meaning of the electronic signature (e.g. approval, authoring)")
    hash: str = Field(description="Cryptographic checksum hash validating the document state")
