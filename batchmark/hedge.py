"""Hedged request policy: launch a speculative duplicate request after a delay."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from batchmark.runner import JobResult


@dataclass
class HedgePolicy:
    delay_seconds: float = 0.0
    max_hedges: int = 1
    enabled: bool = False

    def __post_init__(self) -> None:
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        if self.max_hedges < 1:
            raise ValueError("max_hedges must be >= 1")

    def should_hedge(self) -> bool:
        return self.enabled and self.delay_seconds >= 0


def make_hedge_policy(
    delay_seconds: float = 0.0,
    max_hedges: int = 1,
    enabled: bool = False,
) -> HedgePolicy:
    return HedgePolicy(delay_seconds=delay_seconds, max_hedges=max_hedges, enabled=enabled)


def run_with_hedge(
    job: Callable[[], JobResult],
    policy: Optional[HedgePolicy] = None,
) -> JobResult:
    """Run job with optional hedging. Returns the first successful result."""
    if policy is None or not policy.enabled:
        return job()

    result_holder: list[JobResult] = []
    lock = threading.Lock()
    done = threading.Event()

    def attempt() -> None:
        try:
            r = job()
        except Exception as exc:
            r = JobResult(index=0, success=False, duration=0.0, error=str(exc))
        with lock:
            if not done.is_set():
                if r.success or not result_holder:
                    result_holder.clear()
                    result_holder.append(r)
                if r.success:
                    done.set()

    primary = threading.Thread(target=attempt, daemon=True)
    primary.start()

    time.sleep(policy.delay_seconds)

    if not done.is_set():
        hedge = threading.Thread(target=attempt, daemon=True)
        hedge.start()
        hedge.join()

    primary.join()
    done.set()

    return result_holder[0] if result_holder else job()


def describe_hedge_policy(policy: HedgePolicy) -> str:
    if not policy.enabled:
        return "hedge: disabled"
    return f"hedge: enabled, delay={policy.delay_seconds}s, max_hedges={policy.max_hedges}"
