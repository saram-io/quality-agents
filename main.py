"""Command-line interface (CLI) executing the CSV Quality pipeline or the CSA testing suite."""

import asyncio
import json
import os
import sys
from pydantic_ai.models.test import TestModel

from app import (
    QualitySystemDeps,
    SOPDatabase,
    AuditLogger,
    run_quality_pipeline,
    extract_audit_trail,
    regulatory_grounding_agent,
    validation_drafting_agent,
    internal_review_agent,
    run_csa_assurance_suite,
    DEFAULT_CSA_TEST_CASES,
    QualityVectorStoreManager,
)


async def execute_single_scenario(deps: QualitySystemDeps, live_mode: bool) -> None:
    """Executes a single validation document generation scenario."""
    print("\n" + "=" * 80)
    print("      RUNNING SINGLE LIFE CYCLE VALIDATION SCENARIO")
    print("=" * 80)

    scenario_prompt = (
        "Draft a User Requirement Specification (URS) for an automated batch release system "
        "with high-speed digital ingestion."
    )

    print(f"\n[SCENARIO PROMPT]\n\"{scenario_prompt}\"")
    print(f"\nUser context: {deps.current_user} | Target system: {deps.target_system}")

    if not live_mode:
        print("\n--> [INFO] Running in Mock Mode using TestModel (default). Pass '--live' to execute live network calls.")
        with (
            regulatory_grounding_agent.override(model=TestModel()),
            validation_drafting_agent.override(model=TestModel()),
            internal_review_agent.override(model=TestModel()),
        ):
            pipeline_result = await run_quality_pipeline(
                user_input=scenario_prompt,
                deps=deps,
                max_retries=1
            )
    else:
        print(f"\n--> [INFO] Running in Live Mode using active model settings.")
        pipeline_result = await run_quality_pipeline(
            user_input=scenario_prompt,
            deps=deps,
            max_retries=1
        )

    # Print Results
    print("\n" + "=" * 80)
    print("      DRAFTED VALIDATION DOCUMENT DELIVERABLE")
    print("=" * 80)
    draft = pipeline_result.validation_draft
    print(f"Document Type  : {draft.document_type}")
    print(f"GAMP Category  : {pipeline_result.grounding_analysis.gamp_category}")
    print(f"Compliance status: {pipeline_result.final_status}")
    print(f"Revision loops : {pipeline_result.retries_run}")
    print(f"Compliance risk: {pipeline_result.risk_score}")
    
    print("\n--- Document Sections ---")
    for section_title, content in draft.sections.items():
        print(f"\n### {section_title}")
        print(content)
        
    print("\n--- Verification Checklist ---")
    for idx, check in enumerate(draft.verification_checklist, 1):
        print(f"  {idx}. [ ] {check}")

    print("\n" + "=" * 80)
    print("      INTERNAL REVIEW REPORT OUTCOME")
    print("=" * 80)
    review = pipeline_result.review_report
    print(f"Approved                 : {review.approved}")
    print(f"Identified Gaps          : {review.validation_gaps}")
    print(f"Remedial Actions Required: {review.remedial_actions_required}")

    print("\n" + "=" * 80)
    print("      21 CFR PART 11 COMPLIANT AUDIT TRAIL EXTRACTION (from Grounding Run)")
    print("=" * 80)
    
    if pipeline_result.grounding_run_result:
        grounding_audit_json = extract_audit_trail(pipeline_result.grounding_run_result)
        print(grounding_audit_json)
    else:
        print("[INFO] No audit trail extracted because pipeline execution was blocked by compliance guardrails.")


async def execute_csa_suite(deps: QualitySystemDeps, live_mode: bool) -> None:
    """Executes the concurrent CSA automated testing assurance suite."""
    print("\n" + "=" * 80)
    print("      RUNNING CSA AUTOMATED ASSURANCE SUITE")
    print("=" * 80)

    if not live_mode:
        print("\n--> [INFO] Running CSA Suite in Mock Mode using TestModel (default).")
        with (
            regulatory_grounding_agent.override(model=TestModel()),
            validation_drafting_agent.override(model=TestModel()),
            internal_review_agent.override(model=TestModel()),
        ):
            report = await run_csa_assurance_suite(
                test_cases=DEFAULT_CSA_TEST_CASES,
                deps=deps
            )
    else:
        print(f"\n--> [INFO] Running CSA Suite in Live Mode using active model settings.")
        report = await run_csa_assurance_suite(
            test_cases=DEFAULT_CSA_TEST_CASES,
            deps=deps
        )

    # Print CSA Scorecard
    print("\n" + "=" * 80)
    print("      CSA VALIDATION SCORECARD REPORT")
    print("=" * 80)
    print(f"Execution Time      : {report.timestamp}")
    print(f"Total Test Cases    : {report.total_test_cases}")
    print(f"Passed Cases        : {report.passed_cases}")
    print(f"Failed Cases        : {report.failed_cases}")
    print(f"Aggregate Tokens    : {report.aggregate_tokens}")
    print(f"Overall CSV Pass    : {report.passed_cases == report.total_test_cases}")

    print("\n" + "-" * 80)
    print("      INDIVIDUAL TEST CASE OUTCOMES")
    print("-" * 80)
    for result in report.results:
        print(f"\nTest ID: {result.test_id} | Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"  GAMP 5 Category Alignment Verified: {result.gamp_category_verified} (Expected vs Actual: {result.actual_gamp_category})")
        print(f"  Structural Integrity Verified     : {result.structural_integrity_verified}")
        print(f"  Missing Mandatory Sections        : {result.missing_sections}")
        print(f"  Generated Document Sections       : {result.sections_present}")
        print(f"  Compliance Risk Score             : {result.risk_score}")
        print(f"  Validation Status Flag            : {result.validation_status}")
        print(f"  Processing Time                   : {result.execution_duration_sec:.2f}s")
        print(f"  Tokens Consumed                   : {result.tokens_consumed}")


async def main() -> None:
    print("=" * 80)
    print("      LIFE SCIENCES COMPUTER SYSTEM VALIDATION (CSV) PIPELINE (21 CFR Part 11)")
    print("=" * 80)

    # 1. Initialize Mock SOP Database
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
        current_user="quality_director_clara",
        target_system="Batch Ingestion and Automated Release Portal (BIARP)",
        sop_db=db,
        audit_logger=logger,
        vector_store=vector_db,
    )

    # Check CLI options
    live_mode = "--live" in sys.argv
    csa_mode = "--csa" in sys.argv

    if csa_mode:
        await execute_csa_suite(deps, live_mode)
    else:
        await execute_single_scenario(deps, live_mode)

    print("\n" + "=" * 80)
    print("      PIPELINE EXECUTION STEPS (AuditLogger Trail)")
    print("=" * 80)
    for idx, log in enumerate(logger.logs, 1):
        print(f"  {idx:02d}. [{log['step']}] {log['message']}")

    print("\n" + "=" * 80)
    print("      FINISHED SUCCESSFUL PIPELINE RUN")
    print("=" * 80)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
