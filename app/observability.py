"""Observability telemetry engine tracking multi-agent execution performance metrics."""

import threading
from collections import defaultdict
from typing import Dict, List, Any


class QualityTelemetryTracker:
    """Thread-safe telemetry aggregator for tracking system stability and metrics."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls, *args, **kwargs)
                cls._instance._init_tracker()
            return cls._instance

    def _init_tracker(self) -> None:
        """Initialize telemetry store keys."""
        self.lock = threading.Lock()
        self.subagent_latencies: Dict[str, List[float]] = defaultdict(list)
        self.review_total_runs: int = 0
        self.review_rejections: int = 0
        
        # Nested dict structure: {user: {document_type: token_count}}
        self.token_expenditures: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def record_latency(self, agent_name: str, duration_sec: float) -> None:
        """Log duration of a subagent's execution step.

        Args:
            agent_name: Name of the executing subagent.
            duration_sec: The measured processing duration.
        """
        with self.lock:
            self.subagent_latencies[agent_name].append(duration_sec)

    def record_review_result(self, approved: bool) -> None:
        """Track quality review metrics and rejections."""
        with self.lock:
            self.review_total_runs += 1
            if not approved:
                self.review_rejections += 1

    def record_tokens(self, user: str, document_type: str, token_count: int) -> None:
        """Group and record token consumption metrics.

        Args:
            user: Active username execution context.
            document_type: Validation document type (e.g., URS, OQ).
            token_count: Number of tokens consumed in the run.
        """
        with self.lock:
            self.token_expenditures[user][document_type] += token_count

    def reset_metrics(self) -> None:
        """Reset all metric stores (useful for testing)."""
        with self.lock:
            self._init_tracker()

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Exposes aggregated metrics as a JSON-friendly dictionary.

        Exposes GET /api/v1/monitoring/telemetry API format payload.
        """
        with self.lock:
            # Calculate averages
            avg_latencies = {}
            for agent, times in self.subagent_latencies.items():
                avg_latencies[agent] = round(sum(times) / len(times), 3) if times else 0.0

            rejection_rate = (
                round(self.review_rejections / self.review_total_runs, 3)
                if self.review_total_runs > 0
                else 0.0
            )

            # Convert nested defaultdicts to plain dicts for JSON serialization
            tokens_grouped = {
                user: dict(docs) for user, docs in self.token_expenditures.items()
            }

            return {
                "average_latency_sec": avg_latencies,
                "rejection_frequency": rejection_rate,
                "total_runs_reviewed": self.review_total_runs,
                "total_rejections": self.review_rejections,
                "total_tokens_grouped": tokens_grouped,
            }


# Export global tracker instance
telemetry_tracker = QualityTelemetryTracker()
