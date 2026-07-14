"""Execution pipeline orchestrating the sequential run of all CSV validation agents."""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional
from pydantic_ai import AgentRunResult

from .schemas import QualitySystemDeps, GroundingAnalysis, ValidationDraft, ReviewReport
from .vision_verifier import ArchitectureComparison
from .agents import regulatory_grounding_agent, validation_drafting_agent, internal_review_agent
from .monitoring import evaluate_output_risk
from .config import QualitySystemConfig
from .observability import telemetry_tracker
from .prompts.registry import prompt_registry


@dataclass
class PipelineResult:
    """Encapsulates the complete execution trace and output structures of the quality pipeline."""
    grounding_analysis: GroundingAnalysis
    validation_draft: ValidationDraft
    review_report: ReviewReport
    final_status: str
    retries_run: int
    risk_score: float
    grounding_run_result: Optional[AgentRunResult] = None
    drafting_run_result: Optional[AgentRunResult] = None
    review_run_result: Optional[AgentRunResult] = None
    vision_comparison: Optional[ArchitectureComparison] = None


async def run_agent_with_retry_and_fallback(
    agent: Any,
    user_prompt: str,
    deps: QualitySystemDeps,
    usage: Any = None
) -> AgentRunResult:
    """Wrapper that runs an agent with exponential backoff retries and backup fallback models.

    Args:
        agent: The Pydantic AI Agent instance.
        user_prompt: Prompt string sent to the agent.
        deps: quality system runtime dependencies.
        usage: Token usage counter context for nesting / tracking.
    """
    max_retries = QualitySystemConfig.API_MAX_RETRIES
    timeout_sec = QualitySystemConfig.API_TIMEOUT_SEC
    initial_delay = QualitySystemConfig.API_INITIAL_DELAY_SEC
    backoff_factor = QualitySystemConfig.API_BACKOFF_FACTOR

    primary_model = QualitySystemConfig.get_primary_model()
    fallback_model = QualitySystemConfig.get_fallback_model()

    start_time = time.perf_counter()
    last_error = None

    # Check if a model override is active in the current context (e.g. TestModel in unit tests)
    use_override = False
    if hasattr(agent, '_override_model'):
        ov = agent._override_model.get(None)
        if ov is not None:
            use_override = True

    if use_override:
        run_coro = agent.run(user_prompt=user_prompt, deps=deps, usage=usage)
        result = await asyncio.wait_for(run_coro, timeout=timeout_sec)
        duration = time.perf_counter() - start_time
        telemetry_tracker.record_latency(agent.name, duration)
        return result

    model_to_use = primary_model
    is_fallback = False

    for attempt in range(max_retries + 1):
        try:
            with agent.override(model=model_to_use):
                # Wrap the execution in a timeout check
                run_coro = agent.run(user_prompt=user_prompt, deps=deps, usage=usage)
                result = await asyncio.wait_for(run_coro, timeout=timeout_sec)

                # Record latency in telemetry tracker
                duration = time.perf_counter() - start_time
                telemetry_tracker.record_latency(agent.name, duration)

                if is_fallback:
                    deps.audit_logger.log_step(
                        "Pipeline:ModelFallback",
                        f"[WARN] Primary model failed. Fallback model '{fallback_model}' utilized for execution."
                    )
                return result

        except (asyncio.TimeoutError, Exception) as e:
            last_error = e
            deps.audit_logger.log_step(
                f"Pipeline:APIError:Attempt{attempt+1}",
                f"Model '{model_to_use}' failed with error: {str(e)}."
            )

            # Route to secondary fallback model if primary exhausts all retries
            if attempt == max_retries and not is_fallback and primary_model != fallback_model:
                deps.audit_logger.log_step(
                    "Pipeline:FallbackInitiated",
                    f"Primary model '{primary_model}' exhausted all {max_retries} retries. Routing to fallback: '{fallback_model}'."
                )
                model_to_use = fallback_model
                is_fallback = True
                
                # Single execution attempt on fallback model
                try:
                    with agent.override(model=model_to_use):
                        result = await asyncio.wait_for(
                            agent.run(user_prompt=user_prompt, deps=deps, usage=usage),
                            timeout=timeout_sec
                        )
                        duration = time.perf_counter() - start_time
                        telemetry_tracker.record_latency(agent.name, duration)
                        deps.audit_logger.log_step(
                            "Pipeline:ModelFallback",
                            f"[WARN] Primary model failed. Fallback model '{fallback_model}' utilized for execution."
                        )
                        return result
                except Exception as fallback_err:
                    last_error = fallback_err
                    break

            # Backoff delay before retrying
            if attempt < max_retries:
                delay = initial_delay * (backoff_factor ** attempt)
                await asyncio.sleep(delay)

    raise last_error


async def run_quality_pipeline(
    user_input: str,
    deps: QualitySystemDeps,
    max_retries: int = 1,
    diagram_path: Optional[str] = None
) -> PipelineResult:
    """Executes the sequential multi-agent GxP validation pipeline with real-time guardrails."""
    from .guardrails import QualityGuardrailManager, ComplianceViolationException
    from .schemas import GroundingAnalysis, ValidationDraft, ReviewReport

    try:
        # Run Real-Time Input Guardrail Check
        QualityGuardrailManager.validate_input_safety(user_input)
    except ComplianceViolationException as e:
        deps.audit_logger.log_step(
            "Pipeline:CRITICAL_ALERT",
            f"Guardrail blocked execution. Reason: {str(e)}. User: {deps.current_user}"
        )
        grounding_dummy = GroundingAnalysis(
            applicable_sops=[],
            regulatory_constraints=[],
            gamp_category=0,
            retrieved_chunks=[],
            confidence_scores=[]
        )
        draft_dummy = ValidationDraft(
            document_type="BLOCKED",
            sections={"Blocked": f"Input Guardrail Blocked: {str(e)}"},
            verification_checklist=[]
        )
        review_dummy = ReviewReport(
            approved=False,
            validation_gaps=[f"Compliance Block: {str(e)}"]
        )
        return PipelineResult(
            grounding_analysis=grounding_dummy,
            validation_draft=draft_dummy,
            review_report=review_dummy,
            final_status="BLOCKED_BY_GUARDRAIL",
            retries_run=0,
            risk_score=1.0
        )

    try:
        return await _run_pipeline_core(user_input, deps, max_retries, diagram_path)
    except Exception as e:
        deps.audit_logger.log_step(
            "Pipeline:CRITICAL_ALERT",
            f"Guardrail blocked execution. Reason: {str(e)}. User: {deps.current_user}"
        )
        grounding_dummy = GroundingAnalysis(
            applicable_sops=[],
            regulatory_constraints=[],
            gamp_category=deps.gamp_category or 0,
            retrieved_chunks=[],
            confidence_scores=[]
        )
        draft_dummy = ValidationDraft(
            document_type="BLOCKED",
            sections={"Blocked": f"Compliance Result Validation Block: {str(e)}"},
            verification_checklist=[]
        )
        review_dummy = ReviewReport(
            approved=False,
            validation_gaps=[f"Compliance Block: {str(e)}"]
        )
        return PipelineResult(
            grounding_analysis=grounding_dummy,
            validation_draft=draft_dummy,
            review_report=review_dummy,
            final_status="BLOCKED_BY_GUARDRAIL",
            retries_run=0,
            risk_score=1.0
        )


async def _run_pipeline_core(
    user_input: str,
    deps: QualitySystemDeps,
    max_retries: int = 1,
    diagram_path: Optional[str] = None
) -> PipelineResult:
    """Core sequential multi-agent execution logic."""
    from .schemas import GroundingAnalysis, ValidationDraft, ReviewReport

    # Step 1: Regulatory Grounding
    grounding_prompt = f"Analyze regulatory grounding and SOP constraints for system: {user_input}"
    grounding_run_result = await run_agent_with_retry_and_fallback(
        agent=regulatory_grounding_agent,
        user_prompt=grounding_prompt,
        deps=deps
    )
    grounding_analysis = grounding_run_result.output
    
    # Share category with dependencies for validation result validator checks
    deps.gamp_category = grounding_analysis.gamp_category
    
    deps.audit_logger.log_step(
        "Pipeline:GroundingComplete",
        f"GAMP Category: {grounding_analysis.gamp_category}. Applicable SOPs: {grounding_analysis.applicable_sops}"
    )

    from app.queue.tasks import update_job_progress
    update_job_progress(deps.job_id, 30, "Regulatory Grounding completed. Loading Drafting template...")

    # Step 2: Validation Drafting
    drafting_prompt = prompt_registry.get_prompt(
        "validation_drafting",
        {
            "user_input": user_input,
            "gamp_category": grounding_analysis.gamp_category,
            "applicable_sops": ", ".join(grounding_analysis.applicable_sops),
            "regulatory_constraints": ", ".join(grounding_analysis.regulatory_constraints)
        }
    )
    
    # Retrieve and inject past corrections feedback
    from .feedback.injector import retrieve_and_inject_feedback
    feedback_block = retrieve_and_inject_feedback(user_input, deps)
    if feedback_block:
        drafting_prompt += f"\n{feedback_block}"

    prompt_version = prompt_registry.get_prompt_version("validation_drafting")
    deps.audit_logger.log_step(
        "Pipeline:DraftingPromptLoaded",
        f"Loaded prompt template 'validation_drafting' version: {prompt_version}"
    )
    drafting_run_result = await run_agent_with_retry_and_fallback(
        agent=validation_drafting_agent,
        user_prompt=drafting_prompt,
        deps=deps
    )
    validation_draft = drafting_run_result.output
    deps.audit_logger.log_step("Pipeline:DraftingComplete", f"Document Draft created: {validation_draft.document_type}")

    from app.queue.tasks import update_job_progress
    update_job_progress(deps.job_id, 60, "Validation Drafting complete. Initiating multi-modal vision and quality audits...")

    # Step 2.5: Compliance Risk Scan
    risk_score = evaluate_output_risk(validation_draft)
    deps.audit_logger.log_step("Pipeline:RiskScan", f"Compliance risk score evaluated: {risk_score}")

    # Step 2.7: Multi-Modal Vision verification checkpoint (if diagram_path is provided)
    vision_comparison = None
    if diagram_path:
        from .vision_verifier import verify_diagram_against_specs
        vision_comparison = await verify_diagram_against_specs(diagram_path, validation_draft, deps)

    # Step 3: Quality Review Check
    review_prompt = f"Audit the drafted validation document:\n{validation_draft.model_dump_json()}"
    if vision_comparison:
        review_prompt += (
            f"\n\nCRITICAL - Vision Architecture Audit Comparison Results:\n"
            f"- Visual Nodes Detected: {vision_comparison.visual_nodes_detected}\n"
            f"- Structural Discrepancies: {vision_comparison.structural_discrepancies}\n"
            f"- Data Flow Gaps: {vision_comparison.data_flow_gaps}\n"
            f"- Visual Compliance Status: {vision_comparison.compliance_status}\n"
        )
    review_run_result = await run_agent_with_retry_and_fallback(
        agent=internal_review_agent,
        user_prompt=review_prompt,
        deps=deps
    )
    review_report = review_run_result.output
    
    # Inject risk findings if risk threshold is exceeded
    if risk_score >= 0.5:
        review_report.approved = False
        review_report.validation_gaps.append(f"High risk score ({risk_score}) returned from the monitoring compliance scanner.")
        review_report.remedial_actions_required = (review_report.remedial_actions_required or "") + " Resolve compliance red flags in the document."

    # Downgrade review approval if vision verifier detected discrepancies
    if vision_comparison and vision_comparison.compliance_status in ("REJECTED", "DISCREPANCIES_FOUND"):
        review_report.approved = False
        review_report.validation_gaps.append(
            f"Vision Discrepancy Downgrade: The multi-modal architecture vision audit flagged status: '{vision_comparison.compliance_status}'."
        )
        if vision_comparison.structural_discrepancies:
            review_report.remedial_actions_required = (
                (review_report.remedial_actions_required or "") +
                f" Resolve visual diagram discrepancies in spec: {vision_comparison.structural_discrepancies}."
            )

    deps.audit_logger.log_step("Pipeline:ReviewComplete", f"Approval Status: {review_report.approved}")

    # Step 4: Remediation Loop
    retries = 0
    while not review_report.approved and retries < max_retries:
        retries += 1
        deps.audit_logger.log_step(
            "Pipeline:RevisionRequired",
            f"Review rejected. Gaps: {review_report.validation_gaps}. "
            f"Remedial Actions: {review_report.remedial_actions_required}. "
            f"Initiating correction loop (Attempt {retries}/{max_retries})."
        )

        from app.queue.tasks import update_job_progress
        update_job_progress(deps.job_id, 75, f"Remediation required. Running correction loop attempt {retries}...")

        # Re-draft with revision instructions
        re_draft_prompt = (
            f"Revise the drafted URS document for: {user_input}.\n"
            f"Grounding Constraints:\n"
            f"- GAMP Category: Category {grounding_analysis.gamp_category}\n"
            f"- Applicable SOPs: {', '.join(grounding_analysis.applicable_sops)}\n"
            f"- Regulatory Constraints: {', '.join(grounding_analysis.regulatory_constraints)}\n"
            f"CRITICAL: The previous draft failed review with the following gaps:\n"
            f"{', '.join(review_report.validation_gaps)}\n"
            f"You MUST address these gaps using these remedial actions:\n"
            f"{review_report.remedial_actions_required}"
        )
        drafting_run_result = await run_agent_with_retry_and_fallback(
            agent=validation_drafting_agent,
            user_prompt=re_draft_prompt,
            deps=deps
        )
        validation_draft = drafting_run_result.output
        
        # Re-verify diagram against updated specification
        if diagram_path:
            from .vision_verifier import verify_diagram_against_specs
            vision_comparison = await verify_diagram_against_specs(diagram_path, validation_draft, deps)
            
        # Re-evaluate Risk
        risk_score = evaluate_output_risk(validation_draft)
        deps.audit_logger.log_step("Pipeline:Re-RiskScan", f"Revision Attempt {retries} Compliance risk score: {risk_score}")

        # Re-audit
        review_prompt = f"Audit the revised validation document:\n{validation_draft.model_dump_json()}"
        if vision_comparison:
            review_prompt += (
                f"\n\nCRITICAL - Vision Architecture Audit Comparison Results:\n"
                f"- Visual Nodes Detected: {vision_comparison.visual_nodes_detected}\n"
                f"- Structural Discrepancies: {vision_comparison.structural_discrepancies}\n"
                f"- Data Flow Gaps: {vision_comparison.data_flow_gaps}\n"
                f"- Visual Compliance Status: {vision_comparison.compliance_status}\n"
            )
        review_run_result = await run_agent_with_retry_and_fallback(
            agent=internal_review_agent,
            user_prompt=review_prompt,
            deps=deps
        )
        review_report = review_run_result.output
        
        if vision_comparison and vision_comparison.compliance_status in ("REJECTED", "DISCREPANCIES_FOUND"):
            review_report.approved = False
            review_report.validation_gaps.append(
                f"Vision Discrepancy Downgrade: The multi-modal architecture vision audit flagged status: '{vision_comparison.compliance_status}'."
            )

        if risk_score >= 0.5:
            review_report.approved = False
            review_report.validation_gaps.append(f"High risk score ({risk_score}) returned from the monitoring compliance scanner on revision.")
            review_report.remedial_actions_required = (review_report.remedial_actions_required or "") + " Resolve compliance red flags in the document."

        deps.audit_logger.log_step(
            "Pipeline:Re-ReviewComplete",
            f"Revision Attempt {retries} Approval Status: {review_report.approved}"
        )

    # Establish final GxP status flag
    if review_report.approved:
        final_status = "PENDING_HUMAN_SIGNATURE"
        deps.audit_logger.log_step(
            "Pipeline:FinalApproval",
            "Pre-flight automated check APPROVED. Flagged: PENDING_HUMAN_SIGNATURE."
        )
    else:
        final_status = "REJECTED_WITH_GAPS"
        deps.audit_logger.log_step(
            "Pipeline:FinalFailure",
            f"Pre-flight automated check REJECTED after {retries} retries."
        )

    # Record metrics in QualityTelemetryTracker
    telemetry_tracker.record_review_result(review_report.approved)
    total_tokens = (
        grounding_run_result.usage.total_tokens +
        drafting_run_result.usage.total_tokens +
        review_run_result.usage.total_tokens
    )
    telemetry_tracker.record_tokens(
        user=deps.current_user,
        document_type=validation_draft.document_type,
        token_count=total_tokens
    )

    return PipelineResult(
        grounding_analysis=grounding_analysis,
        grounding_run_result=grounding_run_result,
        validation_draft=validation_draft,
        drafting_run_result=drafting_run_result,
        review_report=review_report,
        review_run_result=review_run_result,
        final_status=final_status,
        retries_run=retries,
        risk_score=risk_score,
        vision_comparison=vision_comparison
    )
