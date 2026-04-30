"""Sliding window rate limiter for batchmark jobs."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WindowPolicy:
    """Limits the number of jobs that can start within a rolling time window."""

    max_calls: int = 0          # 0 means unlimited
    window_seconds: float = 1.0
    _timestamps: deque = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_calls < 0:
            raise ValueError("max_calls must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    @property
    def enabled(self) -> bool:
        return self.max_calls > 0

    def _evict_old(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def acquire(self) -> None:
        """Block until a call slot is available in the current window."""
        if not self.enabled:
            return
        while True:
            now = time.monotonic()
            self._evict_old(now)
            if len(self._timestamps) < self.max_calls:
                self._timestamps.append(now)
                return
            sleep_for = self.window_seconds - (now - self._timestamps[0])
            if sleep_for > 0:
                time.sleep(sleep_for)

    def current_count(self) -> int:
        """Return number of calls recorded in the current window."""
        self._evict_old(time.monotonic())
        return len(self._timestamps)


def make_window_policy(
    max_calls: int = 0,
    window_seconds: float = 1.0,
) -> WindowPolicy:
    return WindowPolicy(max_calls=max_calls, window_seconds=window_seconds)


def describe_window_policy(policy: WindowPolicy) -> str:
    if not policy.enabled:
        return "window: unlimited"
    return (
        f"window: {policy.max_calls} calls per {policy.window_seconds:.2f}s"
    )
