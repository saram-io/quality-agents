"""System performance profiling, latency trackers, and cache hit metrics."""

import time
import logging
from typing import Optional
from app.schemas import QualitySystemDeps

logger = logging.getLogger("app.ops.profiler")


class AgentExecutionProfiler:
    """Telemetry collector measuring agent execution performance and efficiency gains."""

    def __init__(self) -> None:
        self.start_time: float = time.perf_counter()
        self.ttft: float = 0.0
        self.latency: float = 0.0
        self.cache_status: str = "CACHE_MISS_FRESH_RUN"
        self.performance_index: float = 0.0
        self.tokens_saved: int = 0

    def mark_first_token(self) -> None:
        """Records time-to-first-token (TTFT) during streaming outputs."""
        self.ttft = time.perf_counter() - self.start_time

    def complete(self, cache_hit: bool, typical_latency: float = 5.0, typical_tokens: int = 2000) -> None:
        """Finalizes latency calculations and evaluates the Performance Index."""
        self.latency = time.perf_counter() - self.start_time
        
        if cache_hit:
            self.cache_status = "CACHE_HIT"
            self.tokens_saved = typical_tokens
            # Performance Index = % of latency reduction vs typical generative run
            if typical_latency > 0:
                self.performance_index = max(0.0, ((typical_latency - self.latency) / typical_latency) * 100.0)
            else:
                self.performance_index = 100.0
        else:
            self.cache_status = "CACHE_MISS_FRESH_RUN"
            self.performance_index = 0.0
            self.tokens_saved = 0

    def log_telemetry(self, deps: QualitySystemDeps) -> None:
        """Writes performance traces and GxP qualification metrics to the audit trail."""
        log_msg = (
            f"[PROFILER] Status: {self.cache_status} | "
            f"Latency: {self.latency:.4f}s | "
            f"TTFT: {self.ttft:.4f}s | "
            f"Performance Index: {self.performance_index:.2f}% | "
            f"Tokens Saved: {self.tokens_saved}"
        )
        logger.info(log_msg)
        deps.audit_logger.log_step("PerformanceProfiler:Telemetry", log_msg)
