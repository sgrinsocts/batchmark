"""Job scheduling with delay and deadline support."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScheduledJob:
    fn: Callable
    delay: float = 0.0          # seconds before job is eligible to run
    deadline: Optional[float] = None  # max seconds from schedule time; None = unlimited
    label: str = ""
    _scheduled_at: float = field(default_factory=time.monotonic, init=False)

    def is_ready(self) -> bool:
        """Return True if the delay period has elapsed."""
        return (time.monotonic() - self._scheduled_at) >= self.delay

    def is_expired(self) -> bool:
        """Return True if deadline has passed."""
        if self.deadline is None:
            return False
        return (time.monotonic() - self._scheduled_at) > self.deadline

    def wait_until_ready(self) -> None:
        """Block until the job is eligible to run."""
        remaining = self.delay - (time.monotonic() - self._scheduled_at)
        if remaining > 0:
            time.sleep(remaining)


def make_scheduled_job(
    fn: Callable,
    delay: float = 0.0,
    deadline: Optional[float] = None,
    label: str = "",
) -> ScheduledJob:
    if delay < 0:
        raise ValueError("delay must be >= 0")
    if deadline is not None and deadline <= 0:
        raise ValueError("deadline must be > 0")
    return ScheduledJob(fn=fn, delay=delay, deadline=deadline, label=label)


def filter_ready(jobs: list[ScheduledJob]) -> list[ScheduledJob]:
    """Return jobs that are ready and not expired."""
    return [j for j in jobs if j.is_ready() and not j.is_expired()]


def filter_expired(jobs: list[ScheduledJob]) -> list[ScheduledJob]:
    """Return jobs that have passed their deadline without running."""
    return [j for j in jobs if j.is_expired()]
