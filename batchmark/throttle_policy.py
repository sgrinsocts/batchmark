"""Composite helper that wires ThrottleConfig into a pipeline step."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult
from batchmark.throttle_config import ThrottleConfig, describe_throttle_config
from batchmark.throttle_runner import run_with_throttle


@dataclass
class ThrottlePolicy:
    """Thin wrapper that pairs a ThrottleConfig with execution helpers."""
    config: ThrottleConfig = field(default_factory=ThrottleConfig)

    @property
    def active(self) -> bool:
        return self.config.is_active()

    def describe(self) -> str:
        return describe_throttle_config(self.config)

    def run(
        self,
        bench_config: BenchmarkConfig,
        job: Callable[[], None],
    ) -> List[JobResult]:
        return run_with_throttle(bench_config, job, throttle=self.config)


def make_throttle_policy(
    enabled: bool = False,
    rate: float = 0.0,
    burst: int = 1,
) -> ThrottlePolicy:
    """Convenience factory; raises ValueError on invalid parameters."""
    cfg = ThrottleConfig(enabled=enabled, rate=rate, burst=burst)
    cfg.validate()
    return ThrottlePolicy(config=cfg)


def describe_policy(policy: ThrottlePolicy) -> str:
    """Return a human-readable summary of the policy."""
    status = "active" if policy.active else "inactive"
    return f"ThrottlePolicy [{status}]: {policy.describe()}"
