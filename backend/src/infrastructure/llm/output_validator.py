"""AI output validation and safety claim check.
Per spec: 'Validate AI responses before displaying them. Never expose malformed AI output directly.'.
"""

import re

from src.domain.exceptions.llm import SafetyValidationFailed
from src.observability.logger import get_logger

logger = get_logger(__name__)

# Pattern to detect hallucinated statements about current-fact warnings or guesses
HALLUCINATION_PATTERNS = [
    r"will flood in \d+ (hours|minutes|mins)",
    r"road (is|will be) closed",
    r"water level will rise by \d+",
    r"bridge is collapsed",
    r"shelter is open at",
    r"call \d+ for shelter",
]


def validate_safety_claims(text: str) -> None:
    """Verify that the AI is not generating claims about road closures, flooding timelines,
    or shelter openings without deterministic support.
    """
    violations = []

    for pattern in HALLUCINATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(
                f"AI generated unverified assertion matching: '{match.group()}'",
            )

    if violations:
        logger.warning(
            "safety_claim_violation_detected", violations=violations, text=text,
        )
        raise SafetyValidationFailed(violations)


def clean_and_validate_response(text: str) -> str:
    """Helper to sanitize and check free-form safety assistant responses."""
    validate_safety_claims(text)
    return text
