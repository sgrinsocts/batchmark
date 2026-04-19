"""Time budget enforcement for batch runs."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TimeBudget:
    """Tracks elapsed time against a maximum allowed duration (seconds)."""
    max_seconds: float
    _start: float = field(default_factory=time.monotonic, init=False, repr=False)

    def elapsed(self) -> float:
        return time.monotonic() - self._start

    def remaining(self) -> float:
        return max(0.0, self.max_seconds - self.elapsed())

    def is_exceeded(self) -> bool:
        return self.elapsed() >= self.max_seconds

    def reset(self) -> None:
        self._start = time.monotonic()


def make_budget(max_seconds: Optional[float]) -> Optional[TimeBudget]:
    """Return a TimeBudget if max_seconds is positive, else None."""
    if max_seconds is None:
        return None
    if max_seconds <= 0:
        raise ValueError(f"max_seconds must be positive, got {max_seconds}")
    return TimeBudget(max_seconds=max_seconds)


def check_budget(budget: Optional[TimeBudget], label: str = "run") -> None:
    """Raise RuntimeError if the budget has been exceeded."""
    if budget is not None and budget.is_exceeded():
        raise RuntimeError(
            f"Time budget exceeded for {label}: "
            f"{budget.elapsed():.2f}s > {budget.max_seconds:.2f}s"
        )
