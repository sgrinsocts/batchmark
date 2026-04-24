"""Wavefront concurrency control: limits the number of jobs that can
advance simultaneously through a processing pipeline stage."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class WavefrontPolicy:
    """Controls how many jobs may be in-flight at any one time."""

    max_in_flight: int = 0          # 0 = unlimited
    acquire_timeout: float = 5.0    # seconds to wait for a slot
    _semaphore: threading.Semaphore = field(init=False, repr=False)
    _active: int = field(default=0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_in_flight < 0:
            raise ValueError("max_in_flight must be >= 0")
        if self.acquire_timeout < 0:
            raise ValueError("acquire_timeout must be >= 0")
        n = self.max_in_flight if self.max_in_flight > 0 else 2 ** 31
        self._semaphore = threading.Semaphore(n)
        self._active = 0

    @property
    def enabled(self) -> bool:
        return self.max_in_flight > 0

    def acquire(self) -> bool:
        """Acquire a slot; returns True on success, False on timeout."""
        acquired = self._semaphore.acquire(timeout=self.acquire_timeout)
        if acquired:
            with self._lock:
                self._active += 1
        return acquired

    def release(self) -> None:
        """Release a previously acquired slot."""
        with self._lock:
            if self._active > 0:
                self._active -= 1
        self._semaphore.release()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active


def make_wavefront_policy(
    max_in_flight: int = 0,
    acquire_timeout: float = 5.0,
) -> WavefrontPolicy:
    return WavefrontPolicy(max_in_flight=max_in_flight, acquire_timeout=acquire_timeout)


def describe_wavefront_policy(policy: WavefrontPolicy) -> str:
    if not policy.enabled:
        return "wavefront: unlimited"
    return (
        f"wavefront: max_in_flight={policy.max_in_flight}, "
        f"acquire_timeout={policy.acquire_timeout}s"
    )
