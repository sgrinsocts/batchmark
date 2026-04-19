"""Runner that respects ScheduledJob delay and deadline constraints."""
from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from batchmark.schedule import ScheduledJob
from batchmark.runner import JobResult


def _execute_scheduled(job: ScheduledJob) -> JobResult:
    """Wait for readiness then run, or return a deadline-expired result."""
    if job.is_expired():
        return JobResult(
            label=job.label,
            success=False,
            duration=0.0,
            error="deadline_expired",
        )
    job.wait_until_ready()
    if job.is_expired():
        return JobResult(
            label=job.label,
            success=False,
            duration=0.0,
            error="deadline_expired_after_wait",
        )
    start = time.monotonic()
    try:
        job.fn()
        return JobResult(
            label=job.label,
            success=True,
            duration=time.monotonic() - start,
        )
    except Exception as exc:  # noqa: BLE001
        return JobResult(
            label=job.label,
            success=False,
            duration=time.monotonic() - start,
            error=str(exc),
        )


def run_scheduled(
    jobs: list[ScheduledJob],
    concurrency: int = 4,
    timeout: Optional[float] = None,
) -> list[JobResult]:
    """Run scheduled jobs with concurrency, honouring delays and deadlines."""
    results: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_execute_scheduled, job): job for job in jobs}
        for future in as_completed(futures, timeout=timeout):
            results.append(future.result())
    return results
