"""Self-healing compliance linter and automated patching subagent."""

import logging
from typing import Dict, Any
from pydantic_ai import Agent, RunContext

from app.schemas import QualitySystemDeps
from app.agents import DEFAULT_MODEL
from app.agents.patch_schemas import SelfHealingReport

logger = logging.getLogger("app.agents.healing")

self_healing_agent: Agent[QualitySystemDeps, SelfHealingReport] = Agent(
    model=DEFAULT_MODEL,
    name="self_healing_agent",
    deps_type=QualitySystemDeps,
    output_type=SelfHealingReport,
    system_prompt=(
        "You are the Automated Self-Healing and Compliance Patching Subagent. "
        "Your task is to analyze compliance/validation gaps in draft URS documents and automatically "
        "construct target compliance patches. "
        "CRITICAL: You are authorized to fix COSMETIC, FORMATTING, and MISSING_CONSTRAINT defects. "
        "However, you are STRICTLY PROHIBITED from patching CRITICAL_VIOLATION issues. "
        "If any defect has severity CRITICAL_VIOLATION, you must output is_healed = False and apply no patches "
        "for that defect, forcing human engineer escalation. "
        "Use the query_healing_standards tool to retrieve correct formatting layout or rule boundaries."
    )
)


@self_healing_agent.tool
def query_healing_standards(ctx: RunContext[QualitySystemDeps], query_text: str) -> str:
    """Queries the corporate standards vector database for correct formatting or compliance guidelines."""
    tenant = ctx.deps.session.tenant_id if ctx.deps.session else None
    results = ctx.deps.vector_store.query_relevant_guidelines(query_text, limit=3, tenant_id=tenant)
    return "\n\n".join([
        f"SOP ID: {r.get('id', 'N/A')}\nContent: {r.get('content', '')}"
        for r in results
    ])


class SelfHealingFailureException(Exception):
    """Exception raised when self-healing linter encounters a CRITICAL_VIOLATION or fails to heal."""
    def __init__(self, report: SelfHealingReport) -> None:
        self.report = report
        super().__init__(
            f"Self-healing halted on Attempt {report.healing_attempt_id} "
            f"due to critical GxP violations or unpatchable defects. Escalated to Human Review."
        )
