"""Input validation exceptions."""


class ValidationError(Exception):
    """Base validation error."""



class InvalidInput(ValidationError):
    """User input failed validation."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid input for '{field}': {reason}")


class UnsupportedLanguage(ValidationError):
    """Requested language is not supported."""

    def __init__(self, language_code: str, supported: list[str]) -> None:
        self.language_code = language_code
        self.supported = supported
        super().__init__(
            f"Language '{language_code}' not supported. Supported: {supported}",
        )


class AlertSourceUnavailable(Exception):
    """External alert source (NDMA, IMD) is unreachable."""

    def __init__(self, source: str, reason: str = "") -> None:
        self.source = source
        self.reason = reason
        super().__init__(f"Alert source '{source}' unavailable: {reason}")
