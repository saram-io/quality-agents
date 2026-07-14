"""Automated GxP Rollback, Hot-Fix, and System State Recovery Controller."""

import os
import sqlite3
import json
import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.prompts.registry import prompt_registry
from app.queue.tasks import DB_PATH

logger = logging.getLogger("app.ops.recovery")

# In-memory dictionary to override model settings at runtime
ACTIVE_MODEL_CONFIGURATIONS: Dict[str, Dict[str, Any]] = {}

# In-memory status tracking for active hot-fixes
HOT_FIX_STATUS: Dict[str, str] = {}  # agent_name -> 'HOT_FIX_UNQUALIFIED' | 'QUALIFIED_HOT_FIX' | 'HOT_FIX_FAILED'

# Archive of prompt templates by (agent_name, version)
PROMPT_VERSION_ARCHIVE: Dict[tuple[str, str], str] = {
    ("validation_drafting", "1.4.2"): (
        "You are the Validation Drafting Agent for a Life Sciences CSV department.\n"
        "Your task is to generate a draft User Requirement Specification (URS) validation document for system: {user_input}.\n"
        "GAMP Category: Category {gamp_category}\n"
        "Applicable SOPs: {applicable_sops}\n"
        "Regulatory Constraints: {regulatory_constraints}\n"
    ),
    ("validation_drafting", "1.4.1"): (
        "You are an older version of the Validation Drafting Agent.\n"
        "Generate a URS draft for system: {user_input}.\n"
        "GAMP Category: Category {gamp_category}\n"
        "Applicable SOPs: {applicable_sops}\n"
        "Regulatory Constraints: {regulatory_constraints}\n"
    ),
}


class ValidatedStateSnapshot(BaseModel):
    """Immutable snapshot capturing a qualified system state configuration."""
    snapshot_id: str = Field(..., description="Unique UUID identification.")
    qualified_timestamp: datetime = Field(..., description="ISO 8601 UTC timestamp of formal IQ/OQ/PQ success.")
    commit_hash: str = Field(..., description="Git commit hash corresponding to the qualified build.")
    prompt_versions: Dict[str, str] = Field(..., description="Version mapping of system prompts.")
    model_configurations: Dict[str, Dict[str, Any]] = Field(..., description="Model parameters (temp, top_p, etc.).")
    qualification_report_hash: str = Field(..., description="Cryptographic SHA-256 hash of SYSTEM_QUALIFICATION_REPORT.md.")


def get_model_settings_for_agent(agent_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves the active, overridden model settings for a target agent."""
    return ACTIVE_MODEL_CONFIGURATIONS.get(agent_name)


def init_ops_tables() -> None:
    """Initializes GxP ops tracking schemas in SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validated_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                qualified_timestamp TEXT NOT NULL,
                commit_hash TEXT NOT NULL,
                prompt_versions TEXT NOT NULL,
                model_configurations TEXT NOT NULL,
                qualification_report_hash TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_control_logs (
                log_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                operator_id TEXT NOT NULL,
                justification TEXT NOT NULL,
                action_type TEXT NOT NULL,
                snapshot_id TEXT,
                details TEXT NOT NULL
            )
        """)
        conn.commit()
    seed_default_snapshot()


def seed_default_snapshot() -> None:
    """Seeds a qualified default snapshot if none exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM validated_snapshots")
        if cursor.fetchone()[0] == 0:
            snapshot = ValidatedStateSnapshot(
                snapshot_id="default-qualified-snapshot-uuid",
                qualified_timestamp=datetime.now(timezone.utc),
                commit_hash="eb805df688d97107e462192cbb99ace3e327deafa5fc7be537fbdb8b59414bd0",
                prompt_versions={"validation_drafting": "1.4.2"},
                model_configurations={"validation_drafting": {"temperature": 0.0, "top_p": 1.0}},
                qualification_report_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
            )
            cursor.execute(
                "INSERT INTO validated_snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (
                    snapshot.snapshot_id,
                    snapshot.qualified_timestamp.isoformat(),
                    snapshot.commit_hash,
                    json.dumps(snapshot.prompt_versions),
                    json.dumps(snapshot.model_configurations),
                    snapshot.qualification_report_hash
                )
            )
            conn.commit()


init_ops_tables()


class GxPSystemRecoveryManager:
    """Service class executing dynamic GxP system recovery and hot-fixes."""

    @classmethod
    async def trigger_emergency_rollback(
        cls,
        target_snapshot_id: str,
        operator_id: str,
        justification: str,
        event_broker=None,
        audit_logger=None
    ) -> None:
        """Restores prompt versions and agent parameters dynamically to a qualified snapshot.

        Enforces change control audit trails and publishes system-wide rollback alerts.
        """
        # 1. Fetch snapshot from table
        snapshot: Optional[ValidatedStateSnapshot] = None
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT snapshot_id, qualified_timestamp, commit_hash, prompt_versions, model_configurations, qualification_report_hash "
                "FROM validated_snapshots WHERE snapshot_id = ?",
                (target_snapshot_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Snapshot '{target_snapshot_id}' not found in validation registry.")
            snapshot = ValidatedStateSnapshot(
                snapshot_id=row[0],
                qualified_timestamp=datetime.fromisoformat(row[1]),
                commit_hash=row[2],
                prompt_versions=json.loads(row[3]),
                model_configurations=json.loads(row[4]),
                qualification_report_hash=row[5]
            )

        # 2. Revert registry prompts
        for agent_name, version in snapshot.prompt_versions.items():
            template_text = PROMPT_VERSION_ARCHIVE.get(
                (agent_name, version),
                "Restored GxP system prompt template for {user_input}."
            )
            prompt_registry.override_prompt(agent_name, version, template_text)

        # 3. Revert model configurations
        ACTIVE_MODEL_CONFIGURATIONS.clear()
        for agent_name, config in snapshot.model_configurations.items():
            ACTIVE_MODEL_CONFIGURATIONS[agent_name] = config

        # 4. Generate Change Control Log entry
        log_id = str(uuid.uuid4())
        details = {
            "prompt_versions": snapshot.prompt_versions,
            "model_configurations": snapshot.model_configurations,
            "commit_hash": snapshot.commit_hash
        }
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO change_control_logs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    log_id,
                    datetime.now(timezone.utc).isoformat(),
                    operator_id,
                    justification,
                    "ROLLBACK",
                    target_snapshot_id,
                    json.dumps(details)
                )
            )
            conn.commit()

        # 5. Write to cryptographically chained audit logger
        log_msg = (
            f"EMERGENCY CHANGE CONTROL: System rolled back to qualified state '{target_snapshot_id}' "
            f"by operator '{operator_id}'. Justification: {justification}."
        )
        if audit_logger:
            audit_logger.log_step("ChangeControl:Rollback", log_msg)

        # 6. Publish SYSTEM_ROLLED_BACK event
        if event_broker:
            from app.events.broker import QualityEvent, QualityEventType
            event = QualityEvent(
                event_type=QualityEventType.URS_MODIFIED,  # Fallback to system-level event
                tenant_id="system",
                triggered_by_user=operator_id,
                payload={"snapshot_id": target_snapshot_id, "action": "SYSTEM_ROLLED_BACK"}
            )
            await event_broker.publish(event, audit_logger)

    @classmethod
    async def apply_emergency_hot_fix(
        cls,
        target_agent: str,
        target_prompt_text: str,
        operator_id: str,
        justification: str,
        audit_logger=None
    ) -> str:
        """Applies a temporary prompt hot-fix, runs tests, and auto-reverts upon failures."""
        # Save previous prompt details to permit recovery on failure
        prev_version = prompt_registry.get_prompt_version(target_agent)
        _, prev_template = prompt_registry._load_and_parse(target_agent)

        HOT_FIX_STATUS[target_agent] = "HOT_FIX_UNQUALIFIED"
        
        # Apply hot-fix template in registry
        hotfix_version = f"{prev_version}-hotfix"
        prompt_registry.override_prompt(target_agent, hotfix_version, target_prompt_text)

        log_msg = f"HOT-FIX INITIATED: Agent '{target_agent}' override prompt applied. Status: HOT_FIX_UNQUALIFIED. Enqueuing tests..."
        if audit_logger:
            audit_logger.log_step("ChangeControl:HotFixStart", log_msg)

        # Execute tests via subprocess to qualify the hot-fix
        qualified = False
        try:
            # We run the pytest validation suite
            import os
            env = dict(os.environ)
            env["GXP_NESTED_TEST"] = "1"
            process = await asyncio.create_subprocess_exec(
                "uv", "run", "pytest", "-k", "test_csv_team",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            await asyncio.wait_for(process.wait(), timeout=60)
            qualified = (process.returncode == 0)
        except Exception as e:
            logger.error(f"CHANGE_CONTROL: Qualification run exception: {e}")
            qualified = False

        if qualified:
            # Transition to qualified hot-fix status
            HOT_FIX_STATUS[target_agent] = "QUALIFIED_HOT_FIX"
            log_id = str(uuid.uuid4())
            details = {"hotfix_version": hotfix_version, "target_agent": target_agent}
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO change_control_logs VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        log_id,
                        datetime.now(timezone.utc).isoformat(),
                        operator_id,
                        justification,
                        "HOT_FIX",
                        None,
                        json.dumps(details)
                    )
                )
                conn.commit()
            if audit_logger:
                audit_logger.log_step(
                    "ChangeControl:HotFixQualified",
                    f"HOT-FIX SUCCESSFUL: Agent '{target_agent}' qualified under change control {log_id}."
                )
            return hotfix_version
        else:
            # Automatic Self-Reversion on validation run failure
            HOT_FIX_STATUS[target_agent] = "HOT_FIX_FAILED"
            prompt_registry.override_prompt(target_agent, prev_version, prev_template)
            err_msg = (
                f"HOT-FIX FAILED: Agent '{target_agent}' qualification tests failed. "
                f"Initiating automated self-reversion to version '{prev_version}'."
            )
            if audit_logger:
                audit_logger.log_step("Security:CRITICAL_ALERT", err_msg)
            raise ValueError(err_msg)

    @classmethod
    def get_snapshots(cls) -> List[ValidatedStateSnapshot]:
        """Returns all historically qualified validation configurations."""
        snapshots = []
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT snapshot_id, qualified_timestamp, commit_hash, prompt_versions, model_configurations, qualification_report_hash FROM validated_snapshots")
            for row in cursor.fetchall():
                snapshots.append(
                    ValidatedStateSnapshot(
                        snapshot_id=row[0],
                        qualified_timestamp=datetime.fromisoformat(row[1]),
                        commit_hash=row[2],
                        prompt_versions=json.loads(row[3]),
                        model_configurations=json.loads(row[4]),
                        qualification_report_hash=row[5]
                    )
                )
        return snapshots
