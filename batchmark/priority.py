"""Priority queue support for ordering batch jobs before execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, List
import heapq


@dataclass(order=True)
class PrioritizedJob:
    priority: int
    job: Callable[[], Any] = field(compare=False)
    label: str = field(default="", compare=False)

    def __call__(self) -> Any:
        return self.job()


class PriorityQueue:
    """Min-heap priority queue for jobs (lower number = higher priority)."""

    def __init__(self) -> None:
        self._heap: List[PrioritizedJob] = []

    def push(self, job: Callable[[], Any], priority: int = 0, label: str = "") -> None:
        heapq.heappush(self._heap, PrioritizedJob(priority=priority, job=job, label=label))

    def pop(self) -> PrioritizedJob:
        if not self._heap:
            raise IndexError("pop from empty PriorityQueue")
        return heapq.heappop(self._heap)

    def peek(self) -> PrioritizedJob:
        if not self._heap:
            raise IndexError("peek at empty PriorityQueue")
        return self._heap[0]

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def drain(self) -> List[PrioritizedJob]:
        """Return all jobs in priority order, emptying the queue."""
        result = []
        while self._heap:
            result.append(heapq.heappop(self._heap))
        return result


def make_priority_queue(jobs: List[tuple]) -> PriorityQueue:
    """Build a PriorityQueue from a list of (priority, job) or (priority, job, label) tuples."""
    pq = PriorityQueue()
    for item in jobs:
        if len(item) == 2:
            priority, job = item
            pq.push(job, priority)
        else:
            priority, job, label = item
            pq.push(job, priority, label)
    return pq
