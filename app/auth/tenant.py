"""User session contexts, GxP role classifications, and tenant isolation layers."""

from pydantic import BaseModel, Field
from enum import Enum


class GxPRole(str, Enum):
    """Granular role definitions enforcing strict human-in-the-loop control boundaries."""
    CSV_ENGINEER = "CSV_ENGINEER"       # Can generate, edit, and run validations. Cannot sign off.
    QUALITY_APPROVER = "QUALITY_APPROVER" # Can audit, review, and execute formal electronic signatures.
    AUDITOR = "AUDITOR"                 # Read-only access to audit logs and qualification run reports.


class UserSession(BaseModel):
    """Pydantic schema representing the validated active user tenant context."""
    user_id: str = Field(..., description="Unique email or user identifier.")
    tenant_id: str = Field(..., description="Unique logical tenant/sponsor ID mapping to database partitions.")
    role: GxPRole = Field(..., description="The verified GxP role assigned to this user.")
