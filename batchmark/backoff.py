"""Backoff strategies for controlling retry delay growth."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

BackoffStrategy = Literal["constant", "linear", "exponential", "fibonacci"]

VALID_STRATEGIES: set[str] = {"constant", "linear", "exponential", "fibonacci"}


@dataclass
class BackoffPolicy:
    strategy: BackoffStrategy = "exponential"
    base: float = 1.0
    factor: float = 2.0
    max_delay: float = 60.0
    _fib_cache: list[float] = field(default_factory=lambda: [1.0, 1.0], init=False, repr=False)

    def __post_init__(self) -> None:
        if self.strategy not in VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy '{self.strategy}'. Must be one of {sorted(VALID_STRATEGIES)}.")
        if self.base < 0:
            raise ValueError("base must be non-negative.")
        if self.factor <= 0:
            raise ValueError("factor must be positive.")
        if self.max_delay < 0:
            raise ValueError("max_delay must be non-negative.")

    def compute(self, attempt: int) -> float:
        """Return delay in seconds for the given attempt (0-indexed)."""
        if attempt < 0:
            raise ValueError("attempt must be >= 0.")
        raw = self._raw_delay(attempt)
        return min(raw, self.max_delay)

    def _raw_delay(self, attempt: int) -> float:
        if self.strategy == "constant":
            return self.base
        if self.strategy == "linear":
            return self.base + self.factor * attempt
        if self.strategy == "exponential":
            return self.base * (self.factor ** attempt)
        if self.strategy == "fibonacci":
            return self._fibonacci(attempt) * self.base
        raise ValueError(f"Unknown strategy: {self.strategy}")

    def _fibonacci(self, n: int) -> float:
        while len(self._fib_cache) <= n:
            self._fib_cache.append(self._fib_cache[-1] + self._fib_cache[-2])
        return self._fib_cache[n]


def make_backoff_policy(
    strategy: str = "exponential",
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 60.0,
) -> BackoffPolicy:
    return BackoffPolicy(strategy=strategy, base=base, factor=factor, max_delay=max_delay)  # type: ignore[arg-type]


def describe_backoff_policy(policy: BackoffPolicy) -> str:
    return (
        f"BackoffPolicy(strategy={policy.strategy}, base={policy.base}, "
        f"factor={policy.factor}, max_delay={policy.max_delay})"
    )
