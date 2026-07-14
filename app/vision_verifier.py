"""Multi-Modal Architecture Verification Agent auditing visual layouts against specs."""

import os
import mimetypes
from typing import List, Optional
from pydantic import BaseModel, Field

from pydantic_ai import Agent, BinaryImage
from app.config import QualitySystemConfig
from app.schemas import QualitySystemDeps, ValidationDraft


class ArchitectureComparison(BaseModel):
    """Structured output from multi-modal architecture verification audits."""
    visual_nodes_detected: List[str] = Field(
        description="List of nodes or components detected visually in the diagram."
    )
    structural_discrepancies: List[str] = Field(
        description="Any mismatch or components seen in diagram but missing in spec, or vice versa."
    )
    data_flow_gaps: List[str] = Field(
        description="Unencrypted communication pathways or missing redundancy details flagged in diagram."
    )
    compliance_status: str = Field(
        description="Final audit verdict. Allowed values: ALIGNED, DISCREPANCIES_FOUND, REJECTED"
    )


VISION_SYSTEM_PROMPT = """You are a hard-headed GxP life sciences system architect auditing a technical schematic diagram.
Your task is to inspect the visual architecture (nodes, data flow channels, external databases, cloud services) and cross-reference it against the drafted technical specification (ValidationDraft).

Check for typical CSV system faults:
1. Unencrypted transmission lines (e.g. raw HTTP, unencrypted FTP/Telnet).
2. Database single-points-of-failure (e.g. no database replicas, no backup channels).
3. Unauthorized third-party integrations or external APIs not explicitly documented.
4. General discrepancies between what is described in the text sections and what is drawn in the schematic.

Examine the image alongside the text specs:
- Classify verdict as 'ALIGNED' if they correspond perfectly and follow safe standards.
- Classify verdict as 'DISCREPANCIES_FOUND' if components mismatch or minor items are omitted.
- Classify verdict as 'REJECTED' if you observe clear regulatory compliance violations (unencrypted channels, missing backups).
"""

# Instantiate the vision verification agent
architecture_vision_agent = Agent(
    model=QualitySystemConfig.get_primary_model(),
    deps_type=QualitySystemDeps,
    output_type=ArchitectureComparison,
    system_prompt=VISION_SYSTEM_PROMPT
)


async def verify_diagram_against_specs(
    diagram_path: str,
    spec_draft: ValidationDraft,
    deps: QualitySystemDeps
) -> ArchitectureComparison:
    """Reads the system schematic image, runs the multi-modal agent comparison, and returns the verdict.

    Args:
        diagram_path: Path to the target system architecture diagram image.
        spec_draft: Technical specification drafted by the validation agent.
        deps: QualitySystemDeps dependency container.
    """
    deps.audit_logger.log_step(
        "VisionVerifier:Start",
        f"Initiating multi-modal vision audit for diagram: '{diagram_path}'"
    )

    if not os.path.exists(diagram_path):
        deps.audit_logger.log_step(
            "VisionVerifier:Error",
            f"Diagram diagram_path not found: {diagram_path}. Returning default rejected status."
        )
        return ArchitectureComparison(
            visual_nodes_detected=[],
            structural_discrepancies=[f"System diagram file not found: {diagram_path}"],
            data_flow_gaps=["No data flows can be verified since diagram is missing."],
            compliance_status="REJECTED"
        )

    try:
        with open(diagram_path, "rb") as f:
            image_data = f.read()

        # Deduce mime type dynamically
        mime_type, _ = mimetypes.guess_type(diagram_path)
        if not mime_type:
            mime_type = "image/png"  # fallback default

        image_part = BinaryImage(data=image_data, media_type=mime_type)

        prompt_payload = (
            f"Drafted Validation Specification details:\n"
            f"Document Type: {spec_draft.document_type}\n"
            f"Sections:\n"
            f"{spec_draft.model_dump_json(indent=2)}\n\n"
            f"Analyze and audit the provided diagram against these specification details."
        )

        # Run multi-modal verification
        result = await architecture_vision_agent.run(
            [image_part, prompt_payload],
            deps=deps
        )
        deps.audit_logger.log_step(
            "VisionVerifier:Complete",
            f"Vision audit complete. Verdict: {result.output.compliance_status}. "
            f"Detected nodes: {result.output.visual_nodes_detected}"
        )
        return result.output

    except Exception as e:
        # GxP Error Isolation: Log exception and keep system active by returning discrepancy status
        deps.audit_logger.log_step(
            "VisionVerifier:Exception",
            f"Error during vision processing: {str(e)}. Returning isolated failure status."
        )
        return ArchitectureComparison(
            visual_nodes_detected=[],
            structural_discrepancies=[f"Visual engine execution failure: {str(e)}"],
            data_flow_gaps=[],
            compliance_status="DISCREPANCIES_FOUND"
        )
