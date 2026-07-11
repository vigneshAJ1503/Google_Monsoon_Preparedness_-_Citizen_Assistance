"""Domain exceptions for LLM/AI-related errors."""


class LLMError(Exception):
    """Base LLM domain error."""



class InvalidAIResponse(LLMError):
    """LLM returned a response that failed schema or safety validation."""

    def __init__(self, reason: str, raw_response: str = "") -> None:
        self.reason = reason
        self.raw_response = raw_response[
            :500
        ]  # Truncate to avoid logging huge responses
        super().__init__(f"Invalid AI response: {reason}")


class LLMTimeout(LLMError):
    """LLM call exceeded the configured timeout."""

    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(f"LLM call timed out after {timeout_seconds}s")


class SafetyValidationFailed(LLMError):
    """LLM response contained claims that failed safety validation."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(f"Safety validation failed: {', '.join(violations)}")
