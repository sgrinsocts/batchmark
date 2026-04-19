"""Run jobs from a PriorityQueue respecting concurrency limits."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from batchmark.priority import PriorityQueue, PrioritizedJob
from batchmark.runner import JobResult
from batchmark.config import BenchmarkConfig
import time


def run_priority_queue(
    pq: PriorityQueue,
    config: BenchmarkConfig,
) -> List[JobResult]:
    """Execute all jobs in the queue in priority order with bounded concurrency."""
    ordered: List[PrioritizedJob] = pq.drain()
    results: List[JobResult] = []

    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = {}
        for idx, pjob in enumerate(ordered):
            fut = executor.submit(_execute, pjob, idx)
            futures[fut] = idx

        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r.index)
    return results


def _execute(pjob: PrioritizedJob, index: int) -> JobResult:
    start = time.perf_counter()
    error: str | None = None
    try:
        pjob()
    except Exception as exc:
        error = str(exc)
    duration = time.perf_counter() - start
    return JobResult(
        index=index,
        label=pjob.label or f"job-{index}",
        duration=duration,
        error=error,
    )
