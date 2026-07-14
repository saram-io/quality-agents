"""Local Deterministic LLM-as-a-Judge Evaluation Framework grading output compliance."""

from enum import Enum
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.agents import DEFAULT_MODEL


class RiskRating(str, Enum):
    """Enforce standardized GxP quality risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvaluationScore(BaseModel):
    """Structured scorecard response from the judge evaluation agent."""
    completeness_score: float = Field(
        description="Score between 0.0 and 1.0 ranking if all requirements/sections were met."
    )
    compliance_risk_rating: RiskRating = Field(
        description="Standardized risk classification (LOW, MEDIUM, or HIGH) based on GxP guidelines."
    )
    justification_notes: str = Field(
        description="Explanatory notes detailing structural deviations, omissions, or compliance risks."
    )


# Instantiate the Judge Agent
evaluation_judge_agent: Agent[None, EvaluationScore] = Agent(
    model=DEFAULT_MODEL,
    name="evaluation_judge_agent",
    output_type=EvaluationScore,
    system_prompt=(
        "You are an expert Life Sciences Computer System Validation (CSV) Auditor "
        "and a deterministic LLM-as-a-Judge. Your task is to audit drafted validation documents "
        "against their target input requirements.\n"
        "Evaluate the following aspects:\n"
        "1. Completeness: Check if all technical requirements are mapped to sections (score 0.0 to 1.0).\n"
        "2. Compliance Risk: Search for red flags (e.g. self-modifying code, bypassed reviews, "
        "missing audit trails). Assign HIGH if present, MEDIUM if partially addressed, or LOW if clean.\n"
        "3. Clear justification notes for your rating."
    )
)


async def evaluate_prompt_iteration(test_input: str, generated_output: str) -> EvaluationScore:
    """Orchestrates the evaluation loop passing test criteria to the Judge Agent.

    Args:
        test_input: The raw requirements or functionality checklist.
        generated_output: The generated draft validation documentation text.

    Returns:
        EvaluationScore containing structured judge outputs.
    """
    prompt = (
        f"Target System Requirements:\n"
        f"\"\"\"\n{test_input}\n\"\"\"\n\n"
        f"Generated Validation Output Draft:\n"
        f"\"\"\"\n{generated_output}\n\"\"\""
    )

    result = await evaluation_judge_agent.run(prompt)
    return result.output
