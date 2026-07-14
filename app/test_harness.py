"""Computer Software Assurance (CSA) automated verification harness."""

import asyncio
import time
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field

from .schemas import QualitySystemDeps, ValidationDraft
from .pipeline import run_quality_pipeline, PipelineResult


class ValidationTestCase(BaseModel):
    """Pydantic model representing a fixed GxP requirement / change control test case."""
    test_id: str = Field(description="Unique identifier for the CSA test case")
    raw_input: str = Field(description="The requirements or functionality text to test")
    expected_gamp_category: int = Field(description="Expected GAMP 5 software category classification")
    mandatory_sections: List[str] = Field(description="List of document sections that must be generated")


class AssuranceCaseResult(BaseModel):
    """Details the outcomes and verification checks for a single test case execution."""
    test_id: str
    passed: bool
    actual_gamp_category: int
    gamp_category_verified: bool
    sections_present: List[str]
    missing_sections: List[str]
    structural_integrity_verified: bool
    execution_duration_sec: float
    tokens_consumed: int
    validation_status: str
    risk_score: float


class ValidationExecutionReport(BaseModel):
    """Overall CSA automated validation execution report scorecard."""
    timestamp: str
    total_test_cases: int
    passed_cases: int
    failed_cases: int
    aggregate_tokens: int
    results: List[AssuranceCaseResult]


# List of realistic mock ValidationTestCase records (GAMP Category 3, 4, and 5 scenarios)
DEFAULT_CSA_TEST_CASES: List[ValidationTestCase] = [
    ValidationTestCase(
        test_id="CSA-TC-001",
        raw_input="A simple non-configured off-the-shelf laboratory scale calibration calculator software.",
        expected_gamp_category=3,
        mandatory_sections=["Introduction", "Purpose", "System Requirements"]
    ),
    ValidationTestCase(
        test_id="CSA-TC-002",
        raw_input="A configurable LIMS portal to ingest batch data with strict parameter validations and audit logging.",
        expected_gamp_category=4,
        mandatory_sections=["Introduction", "Functional Specifications", "Risk Assessment"]
    ),
    ValidationTestCase(
        test_id="CSA-TC-003",
        raw_input="A custom AI batch release engine implementing self-modifying loops to optimize chemical yields.",
        expected_gamp_category=5,
        # Mandatory sections for a complex Category 5 custom validation draft
        mandatory_sections=["Introduction", "System Requirements", "Detailed Design Specification", "Code Review Checklist"]
    )
]


async def run_single_case(test_case: ValidationTestCase, deps: QualitySystemDeps) -> AssuranceCaseResult:
    """Executes a single validation test case and checks structural/compliance bounds.

    Args:
        test_case: The ValidationTestCase definition.
        deps: quality system runtime dependencies.

    Returns:
        TestCaseResult reporting execution metrics and pass/fail status.
    """
    start_time = time.perf_counter()
    deps.audit_logger.log_step(
        "CSA:TestCaseStart",
        f"Executing CSA verification test case {test_case.test_id} ({test_case.raw_input[:40]}...)"
    )

    try:
        pipeline_result = await run_quality_pipeline(
            user_input=test_case.raw_input,
            deps=deps,
            max_retries=1
        )

        # 1. Verify GAMP category classification
        actual_gamp = pipeline_result.grounding_analysis.gamp_category
        gamp_ok = (actual_gamp == test_case.expected_gamp_category)

        # 2. Verify structural integrity of generated sections
        sections_found = list(pipeline_result.validation_draft.sections.keys())
        missing_sections = [
            sec for sec in test_case.mandatory_sections
            if sec not in pipeline_result.validation_draft.sections
        ]
        structural_ok = (len(missing_sections) == 0)

        # Calculate token consumption across all pipeline runs
        g_usage = pipeline_result.grounding_run_result.usage
        d_usage = pipeline_result.drafting_run_result.usage
        r_usage = pipeline_result.review_run_result.usage
        tokens = g_usage.total_tokens + d_usage.total_tokens + r_usage.total_tokens

        # Pass condition: category match, structural checks pass, risk remains low, pipeline approves
        passed = (
            gamp_ok and 
            structural_ok and 
            pipeline_result.risk_score < 0.5 and 
            pipeline_result.final_status == "PENDING_HUMAN_SIGNATURE"
        )
        validation_status = pipeline_result.final_status
        risk_score = pipeline_result.risk_score

    except Exception as e:
        actual_gamp = -1
        gamp_ok = False
        sections_found = []
        missing_sections = test_case.mandatory_sections
        structural_ok = False
        tokens = 0
        passed = False
        validation_status = f"ERROR: {str(e)}"
        risk_score = 1.0
        deps.audit_logger.log_step(
            "CSA:TestCaseException",
            f"Test case {test_case.test_id} failed with error: {str(e)}"
        )

    duration = time.perf_counter() - start_time
    deps.audit_logger.log_step(
        "CSA:TestCaseComplete",
        f"Test {test_case.test_id} finished. Passed: {passed}. Time: {duration:.2f}s. Tokens: {tokens}."
    )

    return AssuranceCaseResult(
        test_id=test_case.test_id,
        passed=passed,
        actual_gamp_category=actual_gamp,
        gamp_category_verified=gamp_ok,
        sections_present=sections_found,
        missing_sections=missing_sections,
        structural_integrity_verified=structural_ok,
        execution_duration_sec=round(duration, 3),
        tokens_consumed=tokens,
        validation_status=validation_status,
        risk_score=risk_score
    )


async def run_csa_assurance_suite(
    test_cases: List[ValidationTestCase],
    deps: QualitySystemDeps
) -> ValidationExecutionReport:
    """Runs a complete test suite of validation requirements concurrently and compiles the report.

    Args:
        test_cases: List of test cases to run.
        deps: QualitySystemDeps containing databases and loggers.

    Returns:
        ValidationExecutionReport showing results, verification metrics, and aggregate tokens.
    """
    deps.audit_logger.log_step("CSA:SuiteStart", f"Launching CSA automated assurance suite on {len(test_cases)} cases.")
    
    # Run test cases concurrently using asyncio.gather
    tasks = [run_single_case(tc, deps) for tc in test_cases]
    results = await asyncio.gather(*tasks)

    total = len(test_cases)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    aggregate_tokens = sum(r.tokens_consumed for r in results)

    deps.audit_logger.log_step(
        "CSA:SuiteComplete",
        f"CSA Suite run finished. Total: {total}. Passed: {passed}. Failed: {failed}. Tokens: {aggregate_tokens}."
    )

    return ValidationExecutionReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_test_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        aggregate_tokens=aggregate_tokens,
        results=results
    )
