"""Jitter strategies for randomizing delays between retries or scheduled jobs."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

JitterStrategy = Literal["none", "full", "equal", "decorrelated"]


@dataclass
class JitterPolicy:
    strategy: JitterStrategy = "none"
    max_seconds: float = 1.0
    seed: int | None = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")
        if self.strategy not in ("none", "full", "equal", "decorrelated"):
            raise ValueError(f"Unknown jitter strategy: {self.strategy!r}")
        self._rng = random.Random(self.seed)

    def enabled(self) -> bool:
        return self.strategy != "none" and self.max_seconds > 0

    def apply(self, base_delay: float, prev_delay: float | None = None) -> float:
        """Return a jittered delay based on the chosen strategy."""
        if not self.enabled():
            return base_delay
        cap = self.max_seconds
        if self.strategy == "full":
            return self._rng.uniform(0, min(cap, base_delay))
        if self.strategy == "equal":
            half = min(cap, base_delay) / 2
            return half + self._rng.uniform(0, half)
        if self.strategy == "decorrelated":
            prev = prev_delay if prev_delay is not None else base_delay
            return min(cap, self._rng.uniform(base_delay, prev * 3))
        return base_delay


def make_jitter_policy(
    strategy: JitterStrategy = "none",
    max_seconds: float = 1.0,
    seed: int | None = None,
) -> JitterPolicy:
    return JitterPolicy(strategy=strategy, max_seconds=max_seconds, seed=seed)


def describe_jitter_policy(policy: JitterPolicy) -> str:
    if not policy.enabled():
        return "jitter: disabled"
    return f"jitter: strategy={policy.strategy}, max={policy.max_seconds}s"
