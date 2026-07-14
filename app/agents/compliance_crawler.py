"""Policy Drift Detection and Regulatory Scanning Agent."""

import os
import uuid
import logging
from typing import Dict, Any
from pydantic_ai import Agent, RunContext

from app.schemas import QualitySystemDeps
from app.agents import DEFAULT_MODEL
from app.agents.gap_analyzer_schemas import PolicyDriftAssessment

logger = logging.getLogger("app.agents.compliance")

policy_drift_agent: Agent[QualitySystemDeps, PolicyDriftAssessment] = Agent(
    model=DEFAULT_MODEL,
    name="policy_drift_agent",
    deps_type=QualitySystemDeps,
    output_type=PolicyDriftAssessment,
    system_prompt=(
        "You are the Regulatory Policy Drift Agent for a Life Sciences CSV department. "
        "Your task is to analyze updated regulatory guidelines or warning letters, "
        "cross-reference them with our internal SOP database, and detect contradictions or gaps. "
        "CRITICAL: Be extremely analytical, strict, and GxP compliant. "
        "Identify discrepancies in electronic record integrity, Annex 11 updates, or "
        "computer software assurance (CSA) paradigms. "
        "Use the search_internal_sops_for_similarity tool to lookup relevant internal SOP guidelines."
    )
)


@policy_drift_agent.tool
def search_internal_sops_for_similarity(ctx: RunContext[QualitySystemDeps], query_text: str) -> str:
    """Searches the vector database for internal SOP segments corresponding semantically to the query."""
    tenant = ctx.deps.session.tenant_id if ctx.deps.session else None
    results = ctx.deps.vector_store.query_relevant_guidelines(query_text, limit=3, tenant_id=tenant)
    return "\n\n".join([
        f"SOP ID: {r.get('id', 'N/A')}\nContent: {r.get('content', '')}"
        for r in results
    ])


async def evaluate_new_regulatory_document(
    source_name: str,
    new_text: str,
    deps: QualitySystemDeps
) -> PolicyDriftAssessment:
    """Runs the policy drift agent, logs findings, and publishes POLICY_DRIFT_DETECTED events."""
    logger.info(f"POLICY_DRIFT: Evaluating document source '{source_name}'.")
    result = await policy_drift_agent.run(new_text, deps=deps)
    assessment = result.output

    if assessment.is_drift_detected:
        # Publish POLICY_DRIFT_DETECTED event to coordinator
        if deps.event_broker:
            from app.events.broker import QualityEvent, QualityEventType
            event = QualityEvent(
                event_type=QualityEventType.POLICY_DRIFT_DETECTED,
                tenant_id=deps.session.tenant_id if deps.session else "system",
                triggered_by_user=deps.current_user,
                payload={
                    "assessment_id": assessment.assessment_id,
                    "new_regulatory_source": assessment.new_regulatory_source,
                    "severity": assessment.severity_classification.value,
                    "identified_gaps": [gap.model_dump() for gap in assessment.identified_gaps]
                }
            )
            await deps.event_broker.publish(event, deps.audit_logger)

        # Log critical warning in audit log
        log_msg = f"[WARNING] Policy drift identified against new regulation source: {source_name}. Severity: {assessment.severity_classification.value}."
        deps.audit_logger.log_step("Security:CRITICAL_ALERT", log_msg)

    return assessment
