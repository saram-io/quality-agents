"""Compliance monitoring and drift check layer for scanning agent outputs."""

import re
from typing import Dict, List
from .schemas import ValidationDraft


def evaluate_output_risk(draft: ValidationDraft) -> float:
    """Scans validation draft document sections for critical compliance red flags.

    Looks for phrases that violate GxP (Good Practice) or 21 CFR Part 11 guidelines,
    such as bypassing review, editing audit logs, or implementing self-modifying loops.

    Args:
        draft: The generated ValidationDraft model to scan.

    Returns:
        A normalized risk score between 0.0 (Safe) and 1.0 (High Risk / Critical Failure).
    """
    # Define compliance red flag terms with their GxP severity weights
    RED_FLAGS: Dict[str, float] = {
        r"self-modifying\s+loop": 1.0,
        r"bypasses\s+human\s+review": 0.9,
        r"bypass\s+human\s+review": 0.9,
        r"unlogged\s+change": 0.8,
        r"delete\s+audit\s+trail": 1.0,
        r"delete\s+audit\s+log": 1.0,
        r"alter\s+audit\s+trail": 1.0,
        r"alter\s+audit\s+log": 1.0,
        r"bypass\s+electronic\s+signature": 0.9,
        r"bypass\s+signature": 0.9,
        r"automatic\s+approval": 0.7,
        r"override\s+validation": 0.8,
    }

    max_risk = 0.0
    detected_violations: List[str] = []

    # Compile all text content from the draft document sections and checklists
    all_texts: List[str] = [draft.document_type]
    for section_title, content in draft.sections.items():
        all_texts.append(section_title)
        all_texts.append(content)
    for check in draft.verification_checklist:
        all_texts.append(check)

    combined_text = "\n".join(all_texts).lower()

    # Scan for compliance violations
    for pattern, weight in RED_FLAGS.items():
        if re.search(pattern, combined_text):
            detected_violations.append(pattern)
            if weight > max_risk:
                max_risk = weight

    if detected_violations:
        print(f"COMPLIANCE ALERT: Detected potential drift red flags: {detected_violations}. Calculated Risk Score: {max_risk}")
    
    return max_risk
