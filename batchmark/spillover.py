"""Spillover policy: redirect excess jobs to a secondary handler when load exceeds a threshold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class SpilloverPolicy:
    enabled: bool = False
    threshold: int = 0          # max jobs in primary before spillover triggers
    max_spilled: int = 0        # 0 = unlimited
    _spilled: int = field(default=0, init=False, repr=False)
    _primary_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("threshold must be >= 0")
        if self.max_spilled < 0:
            raise ValueError("max_spilled must be >= 0")

    def record_primary(self) -> None:
        self._primary_count += 1

    def should_spill(self) -> bool:
        if not self.enabled:
            return False
        if self.threshold > 0 and self._primary_count < self.threshold:
            return False
        if self.max_spilled > 0 and self._spilled >= self.max_spilled:
            return False
        return True

    def record_spill(self) -> None:
        self._spilled += 1

    @property
    def spilled_count(self) -> int:
        return self._spilled

    def reset(self) -> None:
        self._spilled = 0
        self._primary_count = 0


def make_spillover_policy(
    threshold: int = 0,
    max_spilled: int = 0,
    enabled: bool = True,
) -> SpilloverPolicy:
    if threshold < 0:
        raise ValueError("threshold must be >= 0")
    return SpilloverPolicy(enabled=enabled, threshold=threshold, max_spilled=max_spilled)


def describe_spillover_policy(policy: SpilloverPolicy) -> str:
    if not policy.enabled:
        return "spillover: disabled"
    parts = [f"threshold={policy.threshold}"]
    if policy.max_spilled:
        parts.append(f"max_spilled={policy.max_spilled}")
    return "spillover: " + ", ".join(parts)
