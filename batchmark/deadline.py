"""Per-job deadline enforcement with configurable grace period."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class DeadlinePolicy:
    """Defines a deadline relative to when the policy is armed."""

    seconds: float = 0.0  # 0 means no deadline
    grace_period: float = 0.0

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError("deadline seconds must be >= 0")
        if self.grace_period < 0:
            raise ValueError("grace_period must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.seconds > 0

    def deadline_at(self, start: Optional[float] = None) -> Optional[float]:
        """Return the absolute deadline timestamp, or None if disabled."""
        if not self.enabled:
            return None
        base = start if start is not None else time.monotonic()
        return base + self.seconds + self.grace_period


def make_deadline_policy(
    seconds: float = 0.0,
    grace_period: float = 0.0,
) -> DeadlinePolicy:
    return DeadlinePolicy(seconds=seconds, grace_period=grace_period)


def run_with_deadline(
    fn: Callable[[], object],
    policy: DeadlinePolicy,
) -> object:
    """Run *fn* and raise RuntimeError if the deadline has already passed.

    Note: this is a cooperative check — it verifies the deadline before
    and after execution, but does not preempt a running callable.
    """
    if not policy.enabled:
        return fn()

    start = time.monotonic()
    deadline = policy.deadline_at(start)

    if time.monotonic() > deadline:  # type: ignore[operator]
        raise RuntimeError("Deadline exceeded before job started")

    result = fn()

    if time.monotonic() > deadline:  # type: ignore[operator]
        raise RuntimeError("Deadline exceeded after job completed")

    return result


def describe_deadline_policy(policy: DeadlinePolicy) -> str:
    if not policy.enabled:
        return "deadline: none"
    parts = [f"deadline: {policy.seconds}s"]
    if policy.grace_period:
        parts.append(f"grace: {policy.grace_period}s")
    return ", ".join(parts)
