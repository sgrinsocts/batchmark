"""Drain policy: gracefully flush in-flight jobs before shutdown."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from batchmark.runner import JobResult


@dataclass
class DrainPolicy:
    """Controls how the runner drains pending work on shutdown."""

    enabled: bool = False
    timeout_seconds: float = 30.0
    poll_interval: float = 0.1

    def __post_init__(self) -> None:
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")

    def wait_for_drain(
        self,
        is_empty: Callable[[], bool],
        *,
        on_timeout: Optional[Callable[[], None]] = None,
    ) -> bool:
        """Block until the queue is empty or timeout is reached.

        Returns True if drained cleanly, False if timed out.
        """
        if not self.enabled:
            return True

        deadline = time.monotonic() + self.timeout_seconds
        while not is_empty():
            if time.monotonic() >= deadline:
                if on_timeout is not None:
                    on_timeout()
                return False
            time.sleep(self.poll_interval)
        return True


def make_drain_policy(
    enabled: bool = False,
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.1,
) -> DrainPolicy:
    """Construct and validate a DrainPolicy."""
    return DrainPolicy(
        enabled=enabled,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
    )


def describe_drain_policy(policy: DrainPolicy) -> str:
    """Return a human-readable summary of the drain policy."""
    if not policy.enabled:
        return "drain: disabled"
    return (
        f"drain: enabled, timeout={policy.timeout_seconds}s, "
        f"poll={policy.poll_interval}s"
    )
