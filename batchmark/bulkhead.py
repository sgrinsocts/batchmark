"""Bulkhead pattern: isolate job groups into separate concurrency pools.

A bulkhead limits how many concurrent jobs can run within a named partition,
preventing one noisy group from starving others of resources.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class BulkheadPartition:
    """A single named partition with its own semaphore."""

    name: str
    max_concurrent: int
    _semaphore: threading.Semaphore = field(init=False, repr=False)
    _active: int = field(default=0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_concurrent < 1:
            raise ValueError(
                f"Partition '{self.name}': max_concurrent must be >= 1, "
                f"got {self.max_concurrent}"
            )
        self._semaphore = threading.Semaphore(self.max_concurrent)

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Attempt to enter the partition.  Returns False if the bulkhead is full."""
        acquired = self._semaphore.acquire(timeout=timeout if timeout is not None else -1)
        if acquired:
            with self._lock:
                self._active += 1
        return acquired

    def release(self) -> None:
        """Release a slot back to the partition."""
        with self._lock:
            self._active = max(0, self._active - 1)
        self._semaphore.release()

    @property
    def active(self) -> int:
        """Number of jobs currently running inside this partition."""
        with self._lock:
            return self._active


class Bulkhead:
    """Registry of named partitions.  Thread-safe."""

    def __init__(self, default_max: int = 10) -> None:
        if default_max < 1:
            raise ValueError(f"default_max must be >= 1, got {default_max}")
        self._default_max = default_max
        self._partitions: Dict[str, BulkheadPartition] = {}
        self._lock = threading.Lock()

    def partition(self, name: str, max_concurrent: Optional[int] = None) -> BulkheadPartition:
        """Return the partition for *name*, creating it on first access."""
        with self._lock:
            if name not in self._partitions:
                limit = max_concurrent if max_concurrent is not None else self._default_max
                self._partitions[name] = BulkheadPartition(
                    name=name, max_concurrent=limit
                )
            return self._partitions[name]

    def run(self, name: str, fn: Callable, timeout: Optional[float] = None):
        """Run *fn* inside the named partition.

        Raises RuntimeError if the bulkhead is full and *timeout* is exceeded.
        """
        part = self.partition(name)
        acquired = part.acquire(timeout=timeout)
        if not acquired:
            raise RuntimeError(
                f"Bulkhead partition '{name}' is full "
                f"(max_concurrent={part.max_concurrent})"
            )
        try:
            return fn()
        finally:
            part.release()

    def stats(self) -> Dict[str, Dict[str, int]]:
        """Return a snapshot of active counts per partition."""
        with self._lock:
            return {
                name: {"active": p.active, "max_concurrent": p.max_concurrent}
                for name, p in self._partitions.items()
            }


def make_bulkhead(default_max: int = 10) -> Bulkhead:
    """Factory that validates *default_max* and returns a :class:`Bulkhead`."""
    if default_max < 1:
        raise ValueError(f"default_max must be >= 1, got {default_max}")
    return Bulkhead(default_max=default_max)


def describe_bulkhead(bulkhead: Bulkhead) -> str:
    """Human-readable summary of current bulkhead state."""
    lines = ["Bulkhead partitions:"]
    stats = bulkhead.stats()
    if not stats:
        lines.append("  (no partitions registered)")
    else:
        for name, info in sorted(stats.items()):
            lines.append(
                f"  [{name}] active={info['active']} / max={info['max_concurrent']}"
            )
    return "\n".join(lines)
