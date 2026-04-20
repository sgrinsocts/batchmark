"""Runner that applies a jitter policy between job executions."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from batchmark.config import BenchmarkConfig
from batchmark.jitter import JitterPolicy
from batchmark.runner import JobResult, RunSummary


def run_with_jitter(
    config: BenchmarkConfig,
    job: Callable[[int], None],
    policy: JitterPolicy | None = None,
) -> RunSummary:
    """Run all jobs with optional inter-job jitter delay."""
    results: list[JobResult] = []
    prev_delay: float | None = None

    def _execute(index: int) -> JobResult:
        start = time.perf_counter()
        error: str | None = None
        try:
            job(index)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
        duration = time.perf_counter() - start
        return JobResult(index=index, duration=duration, error=error)

    indices = list(range(config.job_count))

    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = {}
        for idx in indices:
            if policy and policy.enabled() and idx > 0:
                delay = policy.apply(0.0, prev_delay)
                prev_delay = delay
                time.sleep(delay)
            futures[executor.submit(_execute, idx)] = idx

        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.index)
    return RunSummary(results=results)
