"""Load shedding policy: drop jobs when system is under pressure."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class SheddingPolicy:
    """Decides whether to accept or shed (drop) incoming jobs."""

    enabled: bool = False
    max_queue_depth: int = 0          # 0 = unlimited
    load_threshold: float = 1.0       # fraction 0.0–1.0; shed when load >= threshold
    sample_window: float = 5.0        # seconds for rolling load estimate
    _submitted: list = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.max_queue_depth < 0:
            raise ValueError("max_queue_depth must be >= 0")
        if not (0.0 < self.load_threshold <= 1.0):
            raise ValueError("load_threshold must be in (0.0, 1.0]")
        if self.sample_window <= 0:
            raise ValueError("sample_window must be > 0")

    def record_submission(self) -> None:
        """Record that a job was submitted (used for load estimation)."""
        now = time.monotonic()
        self._submitted.append(now)
        cutoff = now - self.sample_window
        self._submitted = [t for t in self._submitted if t >= cutoff]

    def current_load(self, capacity: int) -> float:
        """Estimate load as fraction of capacity used in the sample window."""
        if capacity <= 0:
            return 1.0
        now = time.monotonic()
        cutoff = now - self.sample_window
        recent = sum(1 for t in self._submitted if t >= cutoff)
        return min(recent / capacity, 1.0)

    def should_shed(self, queue_depth: int = 0, capacity: int = 1) -> bool:
        """Return True if the job should be dropped."""
        if not self.enabled:
            return False
        if self.max_queue_depth > 0 and queue_depth >= self.max_queue_depth:
            return True
        return self.current_load(capacity) >= self.load_threshold


def make_shedding_policy(
    enabled: bool = False,
    max_queue_depth: int = 0,
    load_threshold: float = 1.0,
    sample_window: float = 5.0,
) -> SheddingPolicy:
    return SheddingPolicy(
        enabled=enabled,
        max_queue_depth=max_queue_depth,
        load_threshold=load_threshold,
        sample_window=sample_window,
    )


def describe_shedding_policy(policy: SheddingPolicy) -> str:
    if not policy.enabled:
        return "shedding: disabled"
    parts = [f"threshold={policy.load_threshold:.0%}"]
    if policy.max_queue_depth > 0:
        parts.append(f"max_queue={policy.max_queue_depth}")
    return "shedding: " + ", ".join(parts)
