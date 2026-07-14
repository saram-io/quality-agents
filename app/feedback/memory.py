"""Self-Correction feedback analyzer extracting structured lessons from human modifications."""

import uuid
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.schemas import ValidationDraft
from app.agents import DEFAULT_MODEL
from app.vector_store import QualityVectorStoreManager, HashEmbeddingModel


class QualityCorrectionLesson(BaseModel):
    """Enforces strict, version-controlled layout for captured quality lessons."""
    lesson_id: str = Field(description="Unique uuid identifier for this correction entry.")
    system_context: str = Field(description="Regulatory standard or system feature concerned.")
    original_ai_text: str = Field(description="The text originally drafted by the AI agent.")
    human_corrected_text: str = Field(description="The final edited and signed copy of the text.")
    extracted_rule: str = Field(description="General, actionable design or compliance rule extracted.")


# Analyzer Agent to determine difference
feedback_analyzer_agent: Agent[None, QualityCorrectionLesson] = Agent(
    model=DEFAULT_MODEL,
    name="feedback_analyzer_agent",
    output_type=QualityCorrectionLesson,
    system_prompt=(
        "You are the CSV Feedback Analyzer Agent.\n"
        "Your task is to analyze differences between an AI-generated draft validation document "
        "and the human-corrected final version.\n"
        "Identify structural changes, formatting improvements, or missed compliance bounds. "
        "Write a structured lesson and formulate an actionable rule (e.g. 'Must always specify backup schedules')."
    )
)


async def extract_correction_lesson(
    original: ValidationDraft,
    corrected: ValidationDraft,
    engineer_notes: str
) -> QualityCorrectionLesson:
    """Invokes feedback analyzer agent to extract a lesson from draft differences."""
    prompt = (
        f"Original AI Draft:\n"
        f"\"\"\"\n{original.model_dump_json()}\n\"\"\"\n\n"
        f"Human Corrected final approved copy:\n"
        f"\"\"\"\n{corrected.model_dump_json()}\n\"\"\"\n\n"
        f"Human Engineer Notes/Rationale:\n"
        f"\"\"\"\n{engineer_notes}\n\"\"\""
    )

    result = await feedback_analyzer_agent.run(prompt)
    lesson = result.output
    # Ensure ID is set
    if not lesson.lesson_id:
        lesson.lesson_id = str(uuid.uuid4())
    return lesson


def store_correction_lesson(
    vector_store: QualityVectorStoreManager,
    lesson: QualityCorrectionLesson
) -> None:
    """Indexes the extracted correction lesson semantically in the vector manager."""
    text_to_index = f"Context: {lesson.system_context}. Rule: {lesson.extracted_rule}"
    embedding = HashEmbeddingModel.compute_embedding(text_to_index)

    vector_store.lessons_index.append({
        "lesson_id": lesson.lesson_id,
        "system_context": lesson.system_context,
        "original_ai_text": lesson.original_ai_text,
        "human_corrected_text": lesson.human_corrected_text,
        "extracted_rule": lesson.extracted_rule,
        "embedding": embedding
    })
