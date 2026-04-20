"""Run a batch of jobs subject to a per-job deadline policy."""

from __future__ import annotations

import concurrent.futures
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.deadline import DeadlinePolicy, run_with_deadline
from batchmark.runner import JobResult, RunSummary


def run_with_deadline_policy(
    jobs: List[Callable[[], object]],
    config: BenchmarkConfig,
    policy: Optional[DeadlinePolicy] = None,
) -> RunSummary:
    """Execute *jobs* with optional per-job deadline enforcement.

    If *policy* is None or disabled every job runs without a deadline check.
    """
    effective_policy = policy or DeadlinePolicy()
    results: List[JobResult] = []

    def _run(index: int, job: Callable[[], object]) -> JobResult:
        import time

        start = time.monotonic()
        try:
            run_with_deadline(job, effective_policy)
            duration = time.monotonic() - start
            return JobResult(index=index, success=True, duration=duration)
        except Exception as exc:  # noqa: BLE001
            duration = time.monotonic() - start
            return JobResult(
                index=index,
                success=False,
                duration=duration,
                error=str(exc),
            )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config.concurrency
    ) as executor:
        futures = {
            executor.submit(_run, i, job): i for i, job in enumerate(jobs)
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.index)
    return RunSummary(results=results)
