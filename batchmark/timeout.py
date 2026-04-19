"""Per-job timeout enforcement using concurrent.futures."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class TimeoutPolicy:
    seconds: Optional[float] = None  # None means no timeout

    def __post_init__(self) -> None:
        if self.seconds is not None and self.seconds <= 0:
            raise ValueError("timeout seconds must be positive")

    @property
    def enabled(self) -> bool:
        return self.seconds is not None


def make_timeout_policy(seconds: Optional[float] = None) -> TimeoutPolicy:
    return TimeoutPolicy(seconds=seconds)


def run_with_timeout(fn: Callable, policy: TimeoutPolicy, *args, **kwargs):
    """Run *fn* with optional timeout. Raises TimeoutError on breach."""
    if not policy.enabled:
        return fn(*args, **kwargs)

    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=policy.seconds)
        except FuturesTimeout:
            future.cancel()
            raise TimeoutError(
                f"job exceeded timeout of {policy.seconds}s"
            )
