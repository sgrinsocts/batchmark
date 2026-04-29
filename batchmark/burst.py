"""Burst policy: allow short-lived spikes above a steady-state rate limit."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

_VALID_STRATEGIES = {"token_bucket", "none"}


@dataclass
class BurstPolicy:
    """Controls how many extra requests can be issued in a burst window."""

    strategy: str = "none"
    steady_rate: float = 0.0   # requests per second; 0 means unlimited
    burst_size: int = 0        # extra tokens allowed above steady rate
    window_seconds: float = 1.0

    # runtime state
    _tokens: float = field(default=0.0, init=False, repr=False)
    _last_refill: float = field(default_factory=time.monotonic, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.strategy not in _VALID_STRATEGIES:
            raise ValueError(f"strategy must be one of {_VALID_STRATEGIES}")
        if self.steady_rate < 0:
            raise ValueError("steady_rate must be >= 0")
        if self.burst_size < 0:
            raise ValueError("burst_size must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._tokens = float(self.burst_size)

    @property
    def enabled(self) -> bool:
        return self.strategy != "none" and self.steady_rate > 0

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now
        new_tokens = elapsed * self.steady_rate
        capacity = self.steady_rate * self.window_seconds + self.burst_size
        self._tokens = min(self._tokens + new_tokens, capacity)

    def acquire(self) -> float:
        """Block until a token is available. Returns wait time in seconds."""
        if not self.enabled:
            return 0.0
        self._refill()
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return 0.0
        # calculate wait for next token
        deficit = 1.0 - self._tokens
        wait = deficit / self.steady_rate
        time.sleep(wait)
        self._tokens = 0.0
        return wait


def make_burst_policy(
    strategy: str = "none",
    steady_rate: float = 0.0,
    burst_size: int = 0,
    window_seconds: float = 1.0,
) -> BurstPolicy:
    return BurstPolicy(
        strategy=strategy,
        steady_rate=steady_rate,
        burst_size=burst_size,
        window_seconds=window_seconds,
    )


def describe_burst_policy(policy: BurstPolicy) -> str:
    if not policy.enabled:
        return "burst: disabled"
    return (
        f"burst: strategy={policy.strategy}, "
        f"steady_rate={policy.steady_rate:.1f} rps, "
        f"burst_size={policy.burst_size}, "
        f"window={policy.window_seconds:.1f}s"
    )
