"""Multi-Agent Collaborative Consensus & Conflict Resolution Engine."""

import uuid
import logging
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from app.schemas import QualitySystemDeps
from app.agents import DEFAULT_MODEL

logger = logging.getLogger("app.agents.consensus")


class ConflictPoint(BaseModel):
    """Immutable model pinpointing a specific discrepancy between agent outputs."""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str = Field(..., description="Agent name introducing the original proposal (e.g. validation_drafting_agent).")
    target_agent: str = Field(..., description="Agent name raising the regulatory objection (e.g. regulatory_grounding_agent).")
    disputed_section: str = Field(..., description="The exact text block or requirement in dispute.")
    reason_for_conflict: str = Field(..., description="Explanatory detail on why the text violates compliance rules.")


class NegotiationTurn(BaseModel):
    """Single turn entry inside a multi-agent debate sequence."""
    turn_number: int
    proposing_agent: str
    proposed_reconciliation: str = Field(..., description="The rewritten compromise or text suggestion.")
    concession_justification: str = Field(..., description="Justification explaining why the rewrite satisfies regulatory and operational bounds.")


class ConsensusResolution(BaseModel):
    """Aggregate resolution record documenting negotiation outcomes."""
    resolution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conflict: ConflictPoint
    negotiation_history: List[NegotiationTurn]
    resolved_text: str = Field(..., description="The final agreed-upon GxP-compliant text, or empty if unresolved.")
    is_consensus_achieved: bool = Field(..., description="True if agreement was programmatically reached.")


class ConsensusFailureException(Exception):
    """Exception raised when programmatic multi-agent negotiation fails to achieve consensus."""
    def __init__(self, resolution: ConsensusResolution) -> None:
        self.resolution = resolution
        super().__init__(
            f"Consensus failed on Conflict {resolution.conflict.conflict_id} "
            f"after {len(resolution.negotiation_history)} turns. Escalated to Human Review."
        )


# =====================================================================
# Dedicated consensus debate participant agents
# =====================================================================

consensus_drafter_agent: Agent[QualitySystemDeps, NegotiationTurn] = Agent(
    model=DEFAULT_MODEL,
    name="consensus_drafter_agent",
    deps_type=QualitySystemDeps,
    output_type=NegotiationTurn,
    system_prompt=(
        "You represent the Validation Drafting Agent in a consensus negotiation. "
        "Your counterpart has raised a regulatory objection against your proposed text. "
        "Analyze the objection, consult applicable SOPs, and propose a compromise version of the text "
        "that satisfies both the comprehensive coverage objective and the regulatory objection. "
        "Provide a clear, logical justification for your compromise suggestion."
    )
)

consensus_regulatory_agent: Agent[QualitySystemDeps, NegotiationTurn] = Agent(
    model=DEFAULT_MODEL,
    name="consensus_regulatory_agent",
    deps_type=QualitySystemDeps,
    output_type=NegotiationTurn,
    system_prompt=(
        "You represent the Regulatory Grounding Agent in a consensus negotiation. "
        "Review the Drafting Agent's proposed compromise text and its justification. "
        "If the compromise is safe, GxP compliant, and satisfies regulatory/SOP boundaries: "
        "accept the proposal, output the agreed text, and justify the concession. "
        "If it is NOT compliant, propose an alternative counter-suggestion and specify why it is still a conflict."
    )
)


async def resolve_validation_conflict(
    conflict: ConflictPoint,
    deps: QualitySystemDeps,
    max_turns: int = 3
) -> ConsensusResolution:
    """Orchestrates an asynchronous multi-turn negotiation debate between agents to resolve conflicts."""
    logger.info(f"CONSENSUS: Resolving conflict {conflict.conflict_id} (Max turns: {max_turns}).")
    
    history: List[NegotiationTurn] = []
    current_text = conflict.disputed_section
    is_consensus_achieved = False
    resolved_text = ""

    for turn_idx in range(1, max_turns + 1):
        # Even/Odd turns alternate: odd turns are drafting proposals, even turns are regulatory reviews.
        if turn_idx % 2 != 0:
            # Drafting turn
            prompt = (
                f"Objection: {conflict.reason_for_conflict}.\n"
                f"Disputed text: {current_text}.\n"
                f"Negotiation History so far: {[t.model_dump() for t in history]}\n"
                f"Formulate Turn {turn_idx} proposing a compromise."
            )
            result = await consensus_drafter_agent.run(prompt, deps=deps)
            turn_data = result.output
            # Ensure turn metadata matches loop counters
            turn_data.turn_number = turn_idx
            turn_data.proposing_agent = "validation_drafting_agent"
            history.append(turn_data)
            current_text = turn_data.proposed_reconciliation
            logger.info(f"CONSENSUS: Turn {turn_idx} proposed rewrite: '{current_text}'")

        else:
            # Regulatory turn
            prompt = (
                f"Original Objection: {conflict.reason_for_conflict}.\n"
                f"Proposed Compromise: {current_text}.\n"
                f"Negotiation History: {[t.model_dump() for t in history]}\n"
                f"Formulate Turn {turn_idx}. Review compliance status. If satisfied, accept and describe reasoning."
            )
            result = await consensus_regulatory_agent.run(prompt, deps=deps)
            turn_data = result.output
            turn_data.turn_number = turn_idx
            turn_data.proposing_agent = "regulatory_grounding_agent"
            history.append(turn_data)
            
            # Simple heuristic or indicator inside LLM justification: if it indicates acceptance/approval
            # without raising counter-objections, we consider consensus achieved.
            # Let's check for keyword "accept" or "concede" or absence of "fail" or "reject"
            just_lower = turn_data.concession_justification.lower()
            if "accept" in just_lower or "approve" in just_lower or "satisfies" in just_lower:
                is_consensus_achieved = True
                resolved_text = turn_data.proposed_reconciliation
                logger.info(f"CONSENSUS: Agreement reached on turn {turn_idx}!")
                break
            else:
                current_text = turn_data.proposed_reconciliation
                logger.info(f"CONSENSUS: Turn {turn_idx} counter-proposal: '{current_text}'")

    # If loop ends without acceptance, consensus has failed
    if not is_consensus_achieved:
        logger.warning(f"CONSENSUS: Failed to achieve agreement after {max_turns} turns.")
        resolved_text = ""

    return ConsensusResolution(
        conflict=conflict,
        negotiation_history=history,
        resolved_text=resolved_text,
        is_consensus_achieved=is_consensus_achieved
    )
