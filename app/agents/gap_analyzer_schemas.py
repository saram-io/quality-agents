"""Strict Pydantic schemas for Policy Drift and Gap Assessments."""

from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class DriftSeverity(str, Enum):
    """Compliance drift threat risk level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH_RISK = "HIGH_RISK"


class PolicyGapItem(BaseModel):
    """Single alignment discrepancy identified between guidelines and internal SOPs."""
    requirement_id: str = Field(..., description="Target regulatory identifier or clause reference.")
    new_regulation_clause: str = Field(..., description="Exact textual statement or description of updated rule.")
    impacted_internal_sop_id: str = Field(..., description="Target reference internal SOP document affected.")
    gap_description: str = Field(..., description="Granular gap details explaining the mismatch.")
    remediation_suggestion: str = Field(..., description="Textual suggestions to upgrade internal SOP compliance.")


class PolicyDriftAssessment(BaseModel):
    """Aggregate regulatory assessment outcome logging policy drift evaluations."""
    assessment_id: str = Field(..., description="Unique assessment UUID.")
    assessment_timestamp: datetime = Field(..., description="UTC timestamp of agent run execution.")
    new_regulatory_source: str = Field(..., description="URL link or document name of source.")
    is_drift_detected: bool = Field(..., description="True if one or more policy alignment gaps are identified.")
    severity_classification: DriftSeverity = Field(..., description="Identified compliance threat classification.")
    identified_gaps: List[PolicyGapItem] = Field(..., description="Detailed list of gap discrepancies.")
