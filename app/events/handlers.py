"""Quality lifecycle event handlers hooking downstream actions into active agents."""

import uuid
import logging
from app.events.broker import QualityEvent
from app.queue.tasks import block_validation_document
from app.queue.worker import TASK_QUEUE

logger = logging.getLogger("app.events.handlers")


async def handle_urs_modification(event: QualityEvent) -> None:
    """Triggered upon modification of user requirements.

    Spins up a background worker task to auto-revise dependent sections.
    """
    payload = event.payload
    new_requirement = payload.get("new_requirement", "")
    target_system = payload.get("target_system", "Automated Calibration System")

    # Generate a fresh UUID job ticket for the automatic draft revision run
    job_id = str(uuid.uuid4())
    
    # Formulate revision instructions
    prompt = (
        f"Generate and revise validation documents based on updated requirements: {new_requirement}."
    )
    
    # Enqueue background task carrying the auto-revision warning flag
    deps_payload = {
        "current_user": event.triggered_by_user,
        "target_system": target_system,
        "session": {
            "user_id": event.triggered_by_user,
            "tenant_id": event.tenant_id,
            "role": "CSV_ENGINEER"
        },
        "auto_revised_warning": f"Draft auto-revised due to upstream URS modification by {event.triggered_by_user}."
    }

    # Dispatch to background task runner queue
    await TASK_QUEUE.put((job_id, prompt, deps_payload, None))
    logger.info(
        f"EVENT_BUS_HANDLER: handle_urs_modification enqueued job {job_id} "
        f"for tenant {event.tenant_id} due to requirement edits."
    )


async def handle_guardrail_trip_notification(event: QualityEvent) -> None:
    """Triggered upon runtime GxP compliance guardrail trips.

    Blocks signing actions on the compromised document ID in the database.
    """
    doc_id = event.payload.get("document_id")
    violation_details = event.payload.get("violation", "Unknown violation.")

    if not doc_id:
        logger.warning("EVENT_BUS_HANDLER: Received guardrail trip event without a target document_id.")
        return

    # Persist blocking status inside SQLite transactionally
    block_validation_document(
        doc_id=doc_id,
        tenant_id=event.tenant_id,
        reason=f"Guardrail violation tripped: {violation_details}"
    )

    # Dispatch high-priority simulated notification alert to QA Approver
    logger.warning(
        f"QA_WEBHOOK_ALERT: [HIGH_PRIORITY] Document {doc_id} under tenant {event.tenant_id} "
        f"has been blocked from signature sign-offs. Reason: {violation_details}"
    )


async def handle_policy_drift_detected(event: QualityEvent) -> None:
    """Triggered upon policy drift detection.

    Persists change control tickets and pushes revision recommendations to dashboard alerts.
    """
    payload = event.payload
    assessment_id = payload.get("assessment_id", str(uuid.uuid4()))
    source = payload.get("new_regulatory_source", "Unknown Regulatory Source")
    severity = payload.get("severity", "LOW")
    gaps = payload.get("identified_gaps", [])

    # Format remediation actions from all gaps
    remediations = []
    for gap in gaps:
        remediations.append(
            f"- Req: {gap.get('requirement_id')}. SOP: {gap.get('impacted_internal_sop_id')}. "
            f"Remediation: {gap.get('remediation_suggestion')}"
        )
    remediation_text = "\n".join(remediations) if remediations else "No gaps identified requiring immediate remediation."

    # Persist change control ticket
    from app.queue.tasks import create_change_control_request, create_dashboard_notification
    create_change_control_request(
        request_id=assessment_id,
        tenant_id=event.tenant_id,
        source=source,
        severity=severity,
        remediation_steps=remediation_text
    )

    # Persist dashboard notification alert
    create_dashboard_notification(
        notification_id=str(uuid.uuid4()),
        tenant_id=event.tenant_id,
        message=f"SOP Revision Recommended: Policy drift identified against new regulation source: {source}."
    )
    logger.info(
        f"EVENT_BUS_HANDLER: handle_policy_drift_detected created Change Control {assessment_id} "
        f"under tenant {event.tenant_id}."
    )
