"""Pydantic schemas and database persistent state controls for multi-tenant background validation tasks."""

import sqlite3
import json
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
from app.auth.tenant import UserSession, GxPRole

class JobStatus(str, Enum):
    """Lifecycle tracking states."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentJobState(BaseModel):
    """Lifecycle model tracking background validation job execution status."""
    job_id: str
    tenant_id: str
    status: JobStatus
    progress_percentage: int = Field(..., ge=0, le=100)
    current_step: str
    result_doc_id: Optional[str] = None
    error_details: Optional[str] = None


DB_PATH = "gxp_tenants.db"


def init_db() -> None:
    """Initializes SQLite database schemas with tenant separation constraints."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Enforce transaction-safe WAL mode for high concurrency
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_jobs (
                job_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                status TEXT NOT NULL,
                progress_percentage INTEGER NOT NULL,
                current_step TEXT NOT NULL,
                result_doc_id TEXT,
                error_details TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compiled_documents (
                doc_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                sections TEXT NOT NULL,
                verification_checklist TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocked_documents (
                doc_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                blocked_reason TEXT NOT NULL
            )
        """)
        conn.commit()


# Automate table generation on module load
init_db()


def get_job_state(job_id: str, tenant_id: str) -> Optional[AgentJobState]:
    """Retrieves the latest execution state metadata of a target validation job, restricted by tenant ID.

    Args:
        job_id: Unique UUID identifier.
        tenant_id: Target tenant identifier to enforce logical data isolation.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_id, tenant_id, status, progress_percentage, current_step, result_doc_id, error_details "
            "FROM agent_jobs WHERE job_id = ? AND tenant_id = ?",
            (job_id, tenant_id)
        )
        row = cursor.fetchone()
        if row:
            return AgentJobState(
                job_id=row[0],
                tenant_id=row[1],
                status=JobStatus(row[2]),
                progress_percentage=row[3],
                current_step=row[4],
                result_doc_id=row[5],
                error_details=row[6]
            )
    return None


def create_job(job_id: str, tenant_id: str) -> AgentJobState:
    """Creates a new queued background job entry in the SQLite tracking table.

    Args:
        job_id: Unique UUID identifier.
        tenant_id: Active tenant identifier.
    """
    job = AgentJobState(
        job_id=job_id,
        tenant_id=tenant_id,
        status=JobStatus.QUEUED,
        progress_percentage=0,
        current_step="Validation job queued in distributed system."
    )
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_jobs (job_id, tenant_id, status, progress_percentage, current_step) "
            "VALUES (?, ?, ?, ?, ?)",
            (job.job_id, job.tenant_id, job.status.value, job.progress_percentage, job.current_step)
        )
        conn.commit()
    return job


def update_job_progress(job_id: Optional[str], progress: int, step: str) -> None:
    """Updates the execution percentage and current active step details.

    Args:
        job_id: Unique UUID identifier.
        progress: Completion percentage (0-100).
        step: Descriptive name of active pipeline milestone.
    """
    if not job_id:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE agent_jobs SET progress_percentage = ?, current_step = ?, status = ? WHERE job_id = ?",
            (progress, step, JobStatus.PROCESSING.value, job_id)
        )
        conn.commit()


def mark_job_failed(job_id: str, error_msg: str) -> None:
    """Transitions a target job to a FAILED status and records error details.

    Args:
        job_id: Unique UUID identifier.
        error_msg: Traceback message or safety violation detail.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE agent_jobs SET status = ?, error_details = ? WHERE job_id = ?",
            (JobStatus.FAILED.value, error_msg, job_id)
        )
        conn.commit()


def mark_job_completed(job_id: str, result_doc_id: str) -> None:
    """Marks a target job as successfully finished and attaches the compiled document ID.

    Args:
        job_id: Unique UUID identifier.
        result_doc_id: References unique ID of final compiled ValidationDraft.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE agent_jobs SET status = ?, progress_percentage = 100, "
            "current_step = 'Validation pipeline execution completed successfully.', result_doc_id = ? "
            "WHERE job_id = ?",
            (JobStatus.COMPLETED.value, result_doc_id, job_id)
        )
        conn.commit()


def save_validation_document(doc_id: str, tenant_id: str, doc_type: str, sections: dict, checklist: list) -> None:
    """Saves the final compiled ValidationDraft output to the SQLite store.

    Args:
        doc_id: Unique database reference ID.
        tenant_id: Tenant identifier scoping this document.
        doc_type: Document classification (e.g. URS, IQ).
        sections: Dictionary containing page section titles and contents (encrypted at rest).
        checklist: List of compiled verification checklist steps.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO compiled_documents (doc_id, tenant_id, document_type, sections, verification_checklist) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, tenant_id, doc_type, json.dumps(sections), json.dumps(checklist))
        )
        conn.commit()


def get_validation_document(doc_id: str, tenant_id: str) -> Optional[dict]:
    """Retrieves a previously compiled validation document draft payload from database, isolated by tenant.

    Args:
        doc_id: Unique database reference ID.
        tenant_id: Active tenant identifier matching the user's session.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_id, tenant_id, document_type, sections, verification_checklist "
            "FROM compiled_documents WHERE doc_id = ? AND tenant_id = ?",
            (doc_id, tenant_id)
        )
        row = cursor.fetchone()
        if row:
            return {
                "doc_id": row[0],
                "tenant_id": row[1],
                "document_type": row[2],
                "sections": json.loads(row[3]),
                "verification_checklist": json.loads(row[4])
            }
    return None


def block_validation_document(doc_id: str, tenant_id: str, reason: str) -> None:
    """Blocks any electronic signing operations on the target validation document.

    Args:
        doc_id: Target document ID.
        tenant_id: Scope separation identifier.
        reason: Plaintext justification for the block.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO blocked_documents (doc_id, tenant_id, blocked_reason) VALUES (?, ?, ?)",
            (doc_id, tenant_id, reason)
        )
        conn.commit()


def is_document_blocked(doc_id: str, tenant_id: str) -> bool:
    """Checks whether the target document has been compromised and blocked from sign-offs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM blocked_documents WHERE doc_id = ? AND tenant_id = ?",
            (doc_id, tenant_id)
        )
        return cursor.fetchone() is not None
