"""GxP-Compliant Semantic Caching and Warm-Start Optimization Engine."""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.schemas import QualitySystemDeps, ValidationDraft
from app.queue.tasks import DB_PATH
from app.vector_store import HashEmbeddingModel


class SemanticCacheEntry(BaseModel):
    """Pydantic model representing a qualified execution cache record."""
    cache_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    input_prompt_hash: str
    input_embedding: List[float]
    system_configuration_fingerprint: str
    sop_dependency_hashes: Dict[str, str]
    cached_output: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def init_semantic_cache() -> None:
    """Initializes the semantic cache database schema."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                cache_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                input_prompt_hash TEXT NOT NULL,
                input_embedding TEXT NOT NULL,
                system_configuration_fingerprint TEXT NOT NULL,
                sop_dependency_hashes TEXT NOT NULL,
                cached_output TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def compute_system_fingerprint() -> str:
    """Generates a SHA-256 fingerprint of the current prompt versions and model configurations."""
    from app.prompts.registry import prompt_registry
    from app.ops.recovery import get_model_settings_for_agent

    # 1. Fetch drafting prompt template details
    prompt_version = prompt_registry.get_prompt_version("validation_drafting") or "1.0.0"
    _, prompt_template = prompt_registry._load_and_parse("validation_drafting")

    # 2. Fetch drafting agent model configs
    model_config = get_model_settings_for_agent("validation_drafting_agent") or {}

    combined = f"{prompt_version}:{prompt_template}:{json.dumps(model_config, sort_keys=True)}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_sop_hashes(sop_ids: List[str], deps: QualitySystemDeps) -> Dict[str, str]:
    """Generates content-based SHA-256 hashes of referenced reference SOP documents."""
    hashes = {}
    for sop_id in sop_ids:
        sop_text = deps.sop_db.get_sop_section(sop_id) or ""
        hashes[sop_id] = hashlib.sha256(sop_text.encode("utf-8")).hexdigest()
    return hashes


async def check_semantic_cache(
    prompt: str,
    tenant_id: str,
    deps: QualitySystemDeps,
    similarity_threshold: float = 0.96
) -> Optional[ValidationDraft]:
    """Interceptors incoming requests to verify semantic similarity against the tenant's cache."""
    # 1. Calculate query embedding
    query_vector = HashEmbeddingModel.compute_embedding(prompt)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    init_semantic_cache()

    # 2. Fetch cache entries for target tenant
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cache_id, input_embedding, system_configuration_fingerprint, "
            "sop_dependency_hashes, cached_output FROM semantic_cache WHERE tenant_id = ?",
            (tenant_id,)
        )
        rows = cursor.fetchall()

    current_system_fp = compute_system_fingerprint()

    for row in rows:
        cache_id, emb_json, sys_fp, sop_hashes_json, output_json = row
        entry_embedding = json.loads(emb_json)

        # 3. Calculate Cosine Similarity (dot product since normalized)
        if len(query_vector) == len(entry_embedding):
            similarity = sum(q * e for q, e in zip(query_vector, entry_embedding))
        else:
            similarity = 0.0

        if similarity >= similarity_threshold:
            # 4. Strict GxP Invalidation Checks
            # A. Check system prompt/model configuration fingerprint
            if sys_fp != current_system_fp:
                invalidate_cache_entry(cache_id)
                deps.audit_logger.log_step(
                    "Cache:Invalidation",
                    f"[WARN] Invalidated cache entry {cache_id} due to system configuration change."
                )
                continue

            # B. Check dependent SOP hashes
            cached_sop_hashes = json.loads(sop_hashes_json)
            current_sop_hashes = compute_sop_hashes(list(cached_sop_hashes.keys()), deps)

            sop_mismatch = False
            for sop_id, cached_hash in cached_sop_hashes.items():
                if current_sop_hashes.get(sop_id) != cached_hash:
                    sop_mismatch = True
                    break

            if sop_mismatch:
                invalidate_cache_entry(cache_id)
                deps.audit_logger.log_step(
                    "Cache:Invalidation",
                    f"[WARN] Invalidated cache entry {cache_id} due to referenced SOP update."
                )
                continue

            # Cache is verified and GxP compliant
            cached_dict = json.loads(output_json)
            return ValidationDraft(**cached_dict)

    return None


def write_semantic_cache(
    prompt: str,
    tenant_id: str,
    draft: ValidationDraft,
    sop_ids: List[str],
    deps: QualitySystemDeps
) -> None:
    """Caches a newly generated, validated draft result with configuration traces."""
    query_vector = HashEmbeddingModel.compute_embedding(prompt)
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    sys_fp = compute_system_fingerprint()
    sop_hashes = compute_sop_hashes(sop_ids, deps)
    cache_id = str(uuid.uuid4())

    init_semantic_cache()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO semantic_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                cache_id,
                tenant_id,
                prompt_hash,
                json.dumps(query_vector),
                sys_fp,
                json.dumps(sop_hashes),
                draft.model_dump_json(),
                datetime.now(timezone.utc).isoformat()
            )
        )
        conn.commit()


def invalidate_cache_entry(cache_id: str) -> None:
    """Removes an invalidated cache entry from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM semantic_cache WHERE cache_id = ?", (cache_id,))
        conn.commit()


# Initialize table on import
init_semantic_cache()
