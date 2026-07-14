"""Middleware to retrieve past corrections and format injection blocks for run contexts."""

from app.schemas import QualitySystemDeps


def retrieve_and_inject_feedback(task_description: str, deps: QualitySystemDeps) -> str:
    """Queries vector database memory store for past lessons matching task description.

    Only matches with a similarity score >= 0.75 are included.

    Args:
        task_description: The user requirements description.
        deps: QualitySystemDeps container.

    Returns:
        Formatted Markdown instructions if matches exist, else empty string.
    """
    if not hasattr(deps, "vector_store") or deps.vector_store is None:
        return ""

    # Semantically search relevant lessons
    matches = deps.vector_store.query_relevant_lessons(task_description, limit=3)
    
    # Filter matching results above similarity threshold >= 0.75
    valid_matches = [m for m in matches if m["similarity_score"] >= 0.75]

    if not valid_matches:
        return ""

    blocks = ["\n### Past Human Corrections & Style Rules Applied to Similar Tasks:"]
    for m in valid_matches:
        blocks.append(
            f"- **Rule**: {m['extracted_rule']}\n"
            f"  **Expected Practice**: {m['human_corrected_text']}"
        )

    # Log injection event
    deps.audit_logger.log_step(
        "FeedbackInjector:Injected",
        f"Injected {len(valid_matches)} relevant past correction lessons into prompt context."
    )

    return "\n".join(blocks)
