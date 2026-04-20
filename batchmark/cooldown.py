"""Cooldown policy: enforces a minimum wait between consecutive job runs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class CooldownPolicy:
    """Tracks last-run timestamps and enforces a minimum gap between runs."""

    seconds: float = 0.0
    _last_run: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError(f"cooldown seconds must be >= 0, got {self.seconds}")

    @property
    def enabled(self) -> bool:
        return self.seconds > 0.0

    def wait(self) -> None:
        """Block until the cooldown period has elapsed since the last call."""
        if not self.enabled:
            return
        elapsed = time.monotonic() - self._last_run
        gap = self.seconds - elapsed
        if gap > 0:
            time.sleep(gap)

    def record(self) -> None:
        """Record the current time as the last-run timestamp."""
        self._last_run = time.monotonic()

    def ready_in(self) -> float:
        """Return seconds remaining in the cooldown (0.0 if already ready)."""
        if not self.enabled:
            return 0.0
        elapsed = time.monotonic() - self._last_run
        return max(0.0, self.seconds - elapsed)


def make_cooldown_policy(seconds: float = 0.0) -> CooldownPolicy:
    """Construct a CooldownPolicy, raising ValueError for invalid input."""
    return CooldownPolicy(seconds=seconds)


def run_with_cooldown(
    jobs: list[Callable[[], object]],
    policy: Optional[CooldownPolicy] = None,
) -> list[object]:
    """Run each job sequentially, applying the cooldown policy between runs."""
    if policy is None:
        policy = CooldownPolicy()
    results: list[object] = []
    for job in jobs:
        policy.wait()
        result = job()
        policy.record()
        results.append(result)
    return results
