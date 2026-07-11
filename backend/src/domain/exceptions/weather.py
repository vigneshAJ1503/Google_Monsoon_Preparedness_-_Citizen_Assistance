"""Domain exceptions for weather-related errors.
Per spec: use domain-specific errors, never empty catch blocks.
"""


class WeatherError(Exception):
    """Base weather domain error."""



class WeatherProviderUnavailable(WeatherError):
    """External weather API is unreachable or returned an error."""

    def __init__(self, provider: str, reason: str = "") -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"Weather provider '{provider}' unavailable: {reason}")


class StaleWeatherData(WeatherError):
    """Weather data exceeds the freshness threshold."""

    def __init__(self, age_seconds: int, threshold_seconds: int) -> None:
        self.age_seconds = age_seconds
        self.threshold_seconds = threshold_seconds
        super().__init__(
            f"Weather data is {age_seconds}s old (threshold: {threshold_seconds}s)",
        )


class UnsupportedLocation(WeatherError):
    """Location is outside the supported coverage area."""

    def __init__(self, latitude: float, longitude: float) -> None:
        self.latitude = latitude
        self.longitude = longitude
        super().__init__(f"Unsupported location: ({latitude}, {longitude})")
