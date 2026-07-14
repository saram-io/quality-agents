"""Strict Pydantic schemas for compliance patching and self-healing operations."""

import uuid
from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class DefectSeverity(str, Enum):
    """Classification of compliance defects based on GxP risk thresholds."""
    COSMETIC = "COSMETIC"
    FORMATTING = "FORMATTING"
    MISSING_CONSTRAINT = "MISSING_CONSTRAINT"
    CRITICAL_VIOLATION = "CRITICAL_VIOLATION"


class ComplianceDefect(BaseModel):
    """Details a single identified validation rule/checklist failure."""
    defect_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    failed_assertion: str = Field(..., description="Description of the checklist requirement failed.")
    error_context: str = Field(..., description="The context paragraph or document section where the defect occurred.")
    severity: DefectSeverity = Field(..., description="Risk severity tier of the defect.")


class CompliancePatch(BaseModel):
    """Automated repair instructions resolving a single compliance defect."""
    original_defect_id: str = Field(..., description="ID of the defect being resolved.")
    patched_section_name: str = Field(..., description="Name of the draft document section being modified.")
    patched_text_diff: str = Field(..., description="Proposed replacement text resolving the defect.")
    healing_justification: str = Field(..., description="Quality/compliance reasoning explaining the resolution.")


class SelfHealingReport(BaseModel):
    """Aggregate healing report documenting defect resolutions."""
    healing_attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    defects_identified: List[ComplianceDefect] = Field(default_factory=list)
    patches_applied: List[CompliancePatch] = Field(default_factory=list)
    is_healed: bool = Field(..., description="True if all defects were patched successfully without critical violations.")
