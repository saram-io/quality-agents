"""Structured GxP schemas and step configurations for IQ/OQ/PQ protocols."""

from typing import Optional
from pydantic import BaseModel, Field


class QualificationStep(BaseModel):
    """Enforces structured GxP documentation for an individual qualification protocol step."""
    step_id: str = Field(description="Unique protocol ID (e.g., IQ-001, OQ-002, PQ-003)")
    protocol_type: str = Field(description="Verification phase type: IQ, OQ, or PQ")
    description: str = Field(description="Description of the test step check")
    expected_result: str = Field(description="Expected acceptance criteria outcomes")
    actual_result: Optional[str] = Field(default=None, description="Observed test results output")
    status: str = Field(default="PENDING", description="Step status: PASS, FAIL, or PENDING")
