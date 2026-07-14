"""Background task queue processing worker executing GxP agents within isolated tenant scopes."""

import asyncio
import uuid
from typing import Dict, Any, Optional

from app.schemas import QualitySystemDeps
from app.database import SOPDatabase, AuditLogger
from app.vector_store import QualityVectorStoreManager
from app.pipeline import run_quality_pipeline
from app.auth.tenant import UserSession, GxPRole
from app.crypto.envelope import encrypt_tenant_field
from app.queue.tasks import (
    update_job_progress,
    mark_job_completed,
    mark_job_failed,
    save_validation_document,
)

# Shared in-process task queue
TASK_QUEUE: asyncio.Queue = asyncio.Queue()


async def async_execute_agent_pipeline(
    job_id: str,
    prompt: str,
    deps_payload: dict,
    diagram_path: Optional[str] = None
) -> None:
    """Instantiates a tenant-isolated context and runs the multi-agent validation pipeline.

    Args:
        job_id: Unique UUID identifier.
        prompt: Ingestion requirements/prompts sent to the agent.
        deps_payload: Serialized dictionary to reconstruct dependencies and active UserSession.
        diagram_path: Optional path to system architecture diagram image.
    """
    update_job_progress(job_id, 10, "Initializing tenant regulatory databases...")

    try:
        # Reconstruct the tenant UserSession context
        session_data = deps_payload.get("session")
        if not session_data:
            raise ValueError("Execution context violation: missing active UserSession.")
            
        session = UserSession(
            user_id=session_data["user_id"],
            tenant_id=session_data["tenant_id"],
            role=GxPRole(session_data["role"])
        )

        # 1. Instantiate fresh GxP context layers
        sop_db = SOPDatabase()
        audit_logger = AuditLogger()
        vector_store = QualityVectorStoreManager()
        
        # Seed only documents matching this tenant's ID
        vector_store.seed_regulatory_knowledge_base(
            sop_db.get_all_documents(),
            tenant_id=session.tenant_id
        )

        # 2. Build full deps context, including the tenant session
        from api import event_broker
        deps = QualitySystemDeps(
            current_user=session.user_id,
            target_system=deps_payload.get("target_system", "Unspecified"),
            sop_db=sop_db,
            audit_logger=audit_logger,
            vector_store=vector_store,
            job_id=job_id,
            session=session,
            event_broker=event_broker
        )

        update_job_progress(job_id, 20, f"Executing isolated grounding for tenant {session.tenant_id}...")

        # 3. Execute quality pipeline
        result = await run_quality_pipeline(
            user_input=prompt,
            deps=deps,
            max_retries=1,
            diagram_path=diagram_path
        )

        if result.final_status == "BLOCKED_BY_GUARDRAIL":
            error_msg = result.validation_draft.sections.get(
                "Blocked",
                "Validation execution blocked by GxP compliance guardrails."
            )
            mark_job_failed(job_id, f"Compliance Guardrail Violation: {error_msg}")
            return

        from app.config import QualitySystemConfig
        if QualitySystemConfig.SHADOW_ENABLED:
            from app.ops.shadow import run_shadow_validation
            asyncio.create_task(
                run_shadow_validation(
                    input_prompt=prompt,
                    production_result=result.validation_draft,
                    deps=deps
                )
            )

        update_job_progress(job_id, 90, "Applying cryptographic envelope encryption to draft sections...")

        # 4. Apply Envelope Encryption to sensitive sections of the validation draft
        draft = result.validation_draft
        warning = deps_payload.get("auto_revised_warning")
        if warning:
            draft.sections["Warning"] = warning

        encrypted_sections = {}
        for title, content in draft.sections.items():
            encrypted_content = encrypt_tenant_field(content, session.tenant_id)
            encrypted_sections[title] = encrypted_content

        # 5. Save validation document scoped to tenant
        doc_id = str(uuid.uuid4())
        save_validation_document(
            doc_id,
            session.tenant_id,
            draft.document_type,
            encrypted_sections,
            draft.verification_checklist
        )

        # 6. Mark completed
        mark_job_completed(job_id, doc_id)

    except Exception as e:
        mark_job_failed(job_id, f"Execution failed due to error: {str(e)}")


async def queue_worker_loop() -> None:
    """Infinite loop fetching and running background validation jobs from the queue."""
    print("BACKGROUND TASK WORKER INITIALIZED AND READY.")
    while True:
        try:
            job_id, prompt, deps_payload, diagram_path = await TASK_QUEUE.get()
            print(f"BACKGROUND WORKER: Fetching Job {job_id} from queue...")
            await async_execute_agent_pipeline(job_id, prompt, deps_payload, diagram_path)
            TASK_QUEUE.task_done()
            print(f"BACKGROUND WORKER: Finished processing Job {job_id}.")
        except asyncio.CancelledError:
            print("BACKGROUND WORKER: Cancellation request received. Shutting down worker...")
            break
        except Exception as e:
            # Prevent background thread crash on unhandled exceptions
            print(f"BACKGROUND WORKER ERROR: {e}")
            await asyncio.sleep(1)
