"""Observable metrics tracking for weather API, LLM, and alert engine.
Uses simple counters/histograms that can be exported to Prometheus.
"""

import time
from dataclasses import dataclass, field


@dataclass
class MetricsStore:
    """In-memory metrics store. Replace with Prometheus client in production."""

    counters: dict[str, int] = field(default_factory=dict)
    histograms: dict[str, list] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1, **labels) -> None:
        key = f"{name}:{labels}" if labels else name
        self.counters[key] = self.counters.get(key, 0) + value

    def observe(self, name: str, value: float, **labels) -> None:
        key = f"{name}:{labels}" if labels else name
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)

    def get_counter(self, name: str) -> int:
        return self.counters.get(name, 0)

    def get_summary(self) -> dict:
        return {
            "counters": dict(self.counters),
            "histogram_counts": {k: len(v) for k, v in self.histograms.items()},
        }


# Singleton
metrics = MetricsStore()


class TimerContext:
    """Context manager for timing operations."""

    def __init__(self, metric_name: str) -> None:
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.monotonic() - self.start_time
        metrics.observe(self.metric_name, elapsed)
        if exc_type:
            metrics.increment(f"{self.metric_name}_errors")
        return False


def timer(metric_name: str) -> TimerContext:
    """Create a timer context for measuring operation latency."""
    return TimerContext(metric_name)
