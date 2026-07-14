#!/usr/bin/env python3
"""CI/CD validation gate verification runner executing headless CSA testing."""

import asyncio
import hashlib
import os
import sys
from datetime import datetime, timezone
from typing import List

from app import (
    QualitySystemDeps,
    SOPDatabase,
    AuditLogger,
    QualityVectorStoreManager,
    run_csa_assurance_suite,
    DEFAULT_CSA_TEST_CASES,
)
from pydantic_ai.models.test import TestModel


def calculate_codebase_checksum() -> str:
    """Computes a SHA256 cryptographic hash of all core application python source files.

    Ensures that the validation report is bound directly to a specific commit/state of code.
    """
    hasher = hashlib.sha256()
    target_dirs = ["app"]
    py_files: List[str] = ["main.py"]

    # Gather all python files recursively in target folders
    for target_dir in target_dirs:
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))

    # Sort files to ensure deterministic hashing order
    py_files.sort()

    for file_path in py_files:
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
        except Exception as e:
            print(f"[WARN] Failed to hash file {file_path}: {e}", file=sys.stderr)

    return hasher.hexdigest()


async def run_ci_gate() -> None:
    print("=" * 80)
    print("      LAUNCHING GxP CI/CD VALIDATION VERIFICATION GATE")
    print("=" * 80)

    # 1. Initialize Mock SOP Database and seed Vector Store
    db = SOPDatabase()
    db._sops["SOP-1024"] = (
        "SOP-1024: Validation Rules for Automated Batch Release Systems. "
        "Any software system implementing automated batch release of GxP materials must undergo "
        "comprehensive pre-flight qualification checking. It requires GAMP Category 4 configured "
        "software validation, a defined testing checklist, and explicit 21 CFR Part 11 signature gates."
    )
    db._sops["SOP-808"] = (
        "SOP-808: Quality Risk Controls for Digital Ingestion. "
        "Digital ingestion of critical batch data requires automated checksum validation, high-speed boundary "
        "checks, and real-time failure state alerting to mitigate risks of corrupted batch logs."
    )

    logger = AuditLogger()
    vector_db = QualityVectorStoreManager()
    vector_db.seed_regulatory_knowledge_base(db.get_all_documents())

    deps = QualitySystemDeps(
        current_user="ci_build_agent",
        target_system="Batch Ingestion and Automated Release Portal (BIARP)",
        sop_db=db,
        audit_logger=logger,
        vector_store=vector_db,
    )

    # 2. Check if running with real credentials or TestModel
    # If the dummy keys are present and no real keys, we run in mock mode
    has_real_keys = (
        "ANTHROPIC_API_KEY" in os.environ and os.environ["ANTHROPIC_API_KEY"] != "dummy-key-for-testing"
    ) or (
        "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"] != "dummy-key-for-testing"
    )

    is_live = has_real_keys and ("--live" in sys.argv)

    print(f"\nMode Selection: {'LIVE API RUNNER' if is_live else 'MOCK RUNNER (TestModel)'}")

    # Run the test suite
    if not is_live:
        from app.agents import regulatory_grounding_agent, validation_drafting_agent, internal_review_agent
        with (
            regulatory_grounding_agent.override(model=TestModel()),
            validation_drafting_agent.override(model=TestModel()),
            internal_review_agent.override(model=TestModel()),
        ):
            report = await run_csa_assurance_suite(DEFAULT_CSA_TEST_CASES, deps)
    else:
        report = await run_csa_assurance_suite(DEFAULT_CSA_TEST_CASES, deps)

    # 3. Calculate Codebase Checksum
    checksum = calculate_codebase_checksum()
    print(f"\nCodebase SHA256 Checksum: {checksum}")

    # 4. Evaluate Quality Gates
    failed_gates = []
    
    # Gate 1: Check for python exceptions / API timeouts (0% failure rate)
    api_failures = 0
    for r in report.results:
        if r.validation_status.startswith("ERROR"):
            api_failures += 1
            
    if api_failures > 0:
        failed_gates.append(f"Gate 1 Failed: {api_failures} API execution exceptions/timeouts detected.")

    # Gate 2: Compliance Red Flags / Risk Score must be exactly 0.0
    high_risks = 0
    for r in report.results:
        if r.risk_score > 0.0:
            high_risks += 1
            
    if high_risks > 0:
        failed_gates.append(f"Gate 2 Failed: {high_risks} test cases triggered compliance drift risks (score > 0.0).")

    # Gate 3: Structural Integrity / Document Section Completeness & GAMP Mappings (Enforced on Live Runs)
    if is_live:
        failed_cases = report.failed_cases
        if failed_cases > 0:
            failed_gates.append(f"Gate 3 Failed: {failed_cases} test cases failed GAMP category matching or mandatory sections.")
    else:
        print("[INFO] Bypassing structural/category matching gates under mock CI environment.")

    # Write IMMUTABLE Report Markdown file
    report_filename = "VALIDATION_RUN_REPORT.md"
    try:
        with open(report_filename, "w") as rf:
            rf.write(f"# GxP Validation Verification Run Report\n\n")
            rf.write(f"> [!IMPORTANT]\n")
            rf.write(f"> **Codebase SHA256 Checksum**: `{checksum}`\n")
            rf.write(f"> **Run Timestamp**: `{report.timestamp}`\n")
            rf.write(f"> **Overall Status**: `{'PASSED' if not failed_gates else 'FAILED'}`\n\n")

            rf.write(f"## Executive Quality Gates Scorecard\n\n")
            rf.write(f"| Quality Gate Check | Target Metric | Actual Value | Status |\n")
            rf.write(f"| :--- | :--- | :--- | :--- |\n")
            rf.write(f"| **Gate 1: API / Exception Errors** | 0% Failure Rate | {api_failures} failures | {'✅ PASS' if api_failures == 0 else '❌ FAIL'} |\n")
            rf.write(f"| **Gate 2: Compliance Drift Risk** | Exactly 0.0 Score | Max score: {max([r.risk_score for r in report.results], default=0.0)} | {'✅ PASS' if high_risks == 0 else '❌ FAIL'} |\n")
            if is_live:
                rf.write(f"| **Gate 3: GAMP & Section Match** | 100% Verification | {report.passed_cases}/{report.total_test_cases} passed | {'✅ PASS' if report.passed_cases == report.total_test_cases else '❌ FAIL'} |\n")
            else:
                rf.write(f"| **Gate 3: GAMP & Section Match** | 100% Verification | Bypassed (Mock Run) | ⚠️ BYPASS |\n")

            rf.write(f"\n## Individual Test Case Results\n\n")
            for r in report.results:
                rf.write(f"### Test Case ID: `{r.test_id}`\n")
                rf.write(f"- **Overall Pass**: `{'PASS' if r.passed else 'FAIL'}`\n")
                rf.write(f"- **GAMP 5 Category Alignment**: Expected vs Actual: {r.actual_gamp_category} (Verified: {r.gamp_category_verified})\n")
                rf.write(f"- **Structural Verification**: {r.structural_integrity_verified} (Missing: {r.missing_sections})\n")
                rf.write(f"- **Compliance Risk Score**: `{r.risk_score}`\n")
                rf.write(f"- **Token expenditure**: `{r.tokens_consumed}` tokens\n")
                rf.write(f"- **Duration**: `{r.execution_duration_sec}s`\n\n")

            rf.write(f"## System Audit Log Trail\n\n")
            rf.write(f"```text\n")
            for log in logger.logs:
                rf.write(f"[{log['step']}] {log['message']}\n")
            rf.write(f"```\n")

        print(f"\n--> Success: Immutable run report generated at '{report_filename}'")
    except Exception as e:
        print(f"[ERROR] Failed to write validation report: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Handle Gates Termination
    if failed_gates:
        print("\n" + "!" * 80, file=sys.stderr)
        print("      GxP CI/CD VALIDATION GATE FAILURE DETECTED", file=sys.stderr)
        print("!" * 80, file=sys.stderr)
        for gate_error in failed_gates:
            print(f"  - [ERROR] {gate_error}", file=sys.stderr)
        print("\nBuild block triggered. Terminating with non-zero exit code.", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 80)
    print("      GxP CI/CD VALIDATION GATE PASSED SUCCESSFULLY")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_ci_gate())
