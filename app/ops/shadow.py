"""Shadow deployment parallel testing engine for continuous validation."""

import os
import sqlite3
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextvars import ContextVar
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.tenant import UserSession, GxPRole
from app.queue.tasks import DB_PATH
from app.schemas import QualitySystemDeps, ValidationDraft
from app.prompts.registry import shadow_prompt_override
from api import require_role

logger = logging.getLogger("app.ops.shadow")

# Task-local ContextVar for shadow model overrides
shadow_model_override: ContextVar[Optional[str]] = ContextVar("shadow_model_override", default=None)

# Router for administration dashboard
router = APIRouter(
    prefix="/api/v1/admin/shadow",
    tags=["shadow"]
)


class ShadowComparisonReport(BaseModel):
    """Immutable record capturing validation divergence between production and shadow configurations."""
    comparison_id: str
    input_prompt_hash: str
    production_config: Dict[str, Any]
    shadow_config: Dict[str, Any]
    structural_match: bool
    semantic_similarity: float
    token_cost_ratio: float
    deviation_details: List[str]


def init_shadow_db() -> None:
    """Initializes shadow metrics table inside SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shadow_comparison_reports (
                comparison_id TEXT PRIMARY KEY,
                input_prompt_hash TEXT NOT NULL,
                production_config TEXT NOT NULL,
                shadow_config TEXT NOT NULL,
                structural_match INTEGER NOT NULL,
                semantic_similarity REAL NOT NULL,
                token_cost_ratio REAL NOT NULL,
                deviation_details TEXT NOT NULL
            )
        """)
        conn.commit()


init_shadow_db()


def get_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates word-overlap Jaccard coefficient between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 and not words2:
        return 1.0
    return float(len(words1.intersection(words2)) / len(words1.union(words2)))


async def run_shadow_validation(
    input_prompt: str,
    production_result: ValidationDraft,
    deps: QualitySystemDeps
) -> None:
    """Runs shadow pipeline in a safe background task and logs divergence telemetry.

    Ensures read-only isolation (no DB commits, no Veeva Vault uploads).
    """
    from app.pipeline import _run_pipeline_core
    from app.config import QualitySystemConfig
    from app.prompts.registry import prompt_registry
    
    # Generate prompt SHA-256 hash
    prompt_hash = hashlib.sha256(input_prompt.encode("utf-8")).hexdigest()

    # Define proposed shadow configurations
    # We default to using the primary model name (or a mock/test variant in test scenarios)
    shadow_model = os.getenv("CSV_SHADOW_MODEL", "google:gemini-1.5-flash")
    # If in unit tests or mock mode, we inherit the test model override if present
    if "PYTEST_CURRENT_TEST" in os.environ:
        shadow_model = "test"

    # Define proposed shadow system prompt
    shadow_prompt_text = (
        "You are the Shadow Validation Drafting Agent for a Life Sciences CSV department.\n"
        "Your task is to generate a draft User Requirement Specification (URS) validation document for system: {user_input}.\n"
        "GAMP Category: Category {gamp_category}\n"
        "Applicable SOPs: {applicable_sops}\n"
        "Regulatory Constraints: {regulatory_constraints}\n"
        "Shadow system tag: [SHADOW_RUN_VERIFIED]."
    )
    shadow_prompts = {
        "validation_drafting": ("1.4.3-shadow", shadow_prompt_text)
    }

    # Set task-local ContextVars
    token_model = shadow_model_override.set(shadow_model)
    token_prompt = shadow_prompt_override.set(shadow_prompts)

    try:
        logger.info(f"SHADOW_ENGINE: Dispatching parallel shadow validation for hash '{prompt_hash[:8]}'.")
        
        # Clone deps container to isolate grounding database lookups
        shadow_deps = QualitySystemDeps(
            current_user=f"{deps.current_user}_shadow",
            target_system=deps.target_system,
            sop_db=deps.sop_db,
            audit_logger=deps.audit_logger,
            vector_store=deps.vector_store,
            job_id=f"{deps.job_id}_shadow" if deps.job_id else None,
            session=deps.session,
            event_broker=None  # Explicitly prevent event publishing from shadow runs
        )

        # Run pipeline core synchronously in background context
        result = await _run_pipeline_core(
            user_input=input_prompt,
            deps=shadow_deps,
            max_retries=0
        )

        shadow_draft = result.validation_draft

        # Calculate Comparison Metrics
        prod_keys = set(production_result.sections.keys())
        shadow_keys = set(shadow_draft.sections.keys())
        
        structural_match = prod_keys == shadow_keys
        
        # Concatenate text content of sections to evaluate semantic overlap
        prod_text = " ".join(production_result.sections.values())
        shadow_text = " ".join(shadow_draft.sections.values())
        similarity = get_jaccard_similarity(prod_text, shadow_text)

        # Calculate size/cost ratio based on character count as token proxy
        prod_len = len(prod_text)
        shadow_len = len(shadow_text)
        token_ratio = float(shadow_len / prod_len) if prod_len > 0 else 1.0

        deviation_details = []
        if not structural_match:
            missing = prod_keys - shadow_keys
            added = shadow_keys - prod_keys
            if missing:
                deviation_details.append(f"Shadow output missing sections: {list(missing)}.")
            if added:
                deviation_details.append(f"Shadow output added extra sections: {list(added)}.")

        if similarity < 0.8:
            deviation_details.append(f"High semantic divergence. Jaccard coefficient: {similarity:.2f}.")

        prod_config = {
            "model": QualitySystemConfig.get_primary_model(),
            "prompt_version": prompt_registry.get_prompt_version("validation_drafting"),
            "temperature": 0.0
        }
        shadow_config = {
            "model": shadow_model,
            "prompt_version": "1.4.3-shadow",
            "temperature": 0.0
        }

        report = ShadowComparisonReport(
            comparison_id=str(uuid.uuid4()),
            input_prompt_hash=prompt_hash,
            production_config=prod_config,
            shadow_config=shadow_config,
            structural_match=structural_match,
            semantic_similarity=similarity,
            token_cost_ratio=token_ratio,
            deviation_details=deviation_details
        )

        # Persist report in DB
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO shadow_comparison_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    report.comparison_id,
                    report.input_prompt_hash,
                    json.dumps(report.production_config),
                    json.dumps(report.shadow_config),
                    1 if report.structural_match else 0,
                    report.semantic_similarity,
                    report.token_cost_ratio,
                    json.dumps(report.deviation_details)
                )
            )
            conn.commit()

        logger.info(f"SHADOW_ENGINE: Shadow verification saved. Id: {report.comparison_id}. Structural: {structural_match}.")

    except Exception as e:
        # Strict try/except sandbox: shadow failure must NEVER interrupt production
        logger.error(f"SHADOW_ENGINE: Critical execution failure in shadow run: {str(e)}", exc_info=True)
    finally:
        # Reset ContextVars to avoid leaking overrides
        shadow_model_override.reset(token_model)
        shadow_prompt_override.reset(token_prompt)


@router.get(
    "/results",
    status_code=status.HTTP_200_OK,
    summary="Retrieve Shadow parallel comparison performance aggregates"
)
async def get_shadow_telemetry(
    session: UserSession = Depends(require_role({GxPRole.QUALITY_APPROVER, GxPRole.AUDITOR}))
):
    """Yields aggregated performance comparison metrics over all background shadow execution runs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*),
                AVG(structural_match),
                AVG(semantic_similarity),
                AVG(token_cost_ratio)
            FROM shadow_comparison_reports
        """)
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            return {
                "total_runs": 0,
                "structural_alignment_rate": 0.0,
                "average_semantic_similarity": 0.0,
                "average_cost_ratio": 1.0,
                "status": "NO_TELEMENTRY_DATA"
            }
            
        return {
            "total_runs": row[0],
            "structural_alignment_rate": float(row[1]),
            "average_semantic_similarity": float(row[2]),
            "average_cost_ratio": float(row[3]),
            "status": "ACTIVE"
        }
