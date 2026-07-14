"""GxP document layouts and tables templates for the CSV Validation Pack."""

from typing import List, Dict, Any


def render_document_history_table(history: List[Dict[str, str]]) -> str:
    """Renders a standard GxP Document Revision history table in Markdown."""
    lines = [
        "| Version | Date | Description of Change | Author / Reviewer | Status |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for row in history:
        lines.append(
            f"| {row.get('version', '')} | {row.get('date', '')} | "
            f"{row.get('description', '')} | {row.get('author', '')} | "
            f"{row.get('status', '')} |"
        )
    return "\n".join(lines)


def render_rtm_table(requirements: List[Dict[str, Any]]) -> str:
    """Renders a standard Requirements Traceability Matrix (RTM) table in Markdown.

    Columns: Requirement ID | Description | Specification Section | Test Protocol ID | Verification Status (PASS/FAIL)
    """
    lines = [
        "| Requirement ID | Description | Specification Section | Test Protocol ID | Verification Status |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for req in requirements:
        lines.append(
            f"| {req.get('req_id', '')} | {req.get('description', '')} | "
            f"{req.get('spec_section', '')} | {req.get('test_id', '')} | "
            f"{req.get('status', 'PENDING')} |"
        )
    return "\n".join(lines)


def render_fmea_table(risks: List[Dict[str, Any]]) -> str:
    """Renders a Failure Mode and Effects Analysis (FMEA) table in Markdown.

    Columns: Feature | Failure Mode | GAMP Classification | Mitigation Criteria | Safety Status
    """
    lines = [
        "| Feature / Function | Potential Failure Mode | GAMP Classification | Mitigation Quality Control | Safety Verification Status |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for risk in risks:
        lines.append(
            f"| {risk.get('feature', '')} | {risk.get('failure_mode', '')} | "
            f"Category {risk.get('gamp_category', '')} | {risk.get('mitigation', '')} | "
            f"{risk.get('status', 'UNVERIFIED')} |"
        )
    return "\n".join(lines)
