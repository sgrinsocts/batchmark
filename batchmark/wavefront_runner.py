"""Runner that enforces a WavefrontPolicy across concurrent jobs."""

from __future__ import annotations

import concurrent.futures
import time
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult
from batchmark.wavefront import WavefrontPolicy


def _execute(
    job: Callable[[], None],
    index: int,
    policy: Optional[WavefrontPolicy],
) -> JobResult:
    if policy is not None and policy.enabled:
        acquired = policy.acquire()
        if not acquired:
            return JobResult(
                index=index,
                success=False,
                duration=0.0,
                error="wavefront acquire timeout",
            )
    start = time.perf_counter()
    error: Optional[str] = None
    try:
        job()
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
    finally:
        if policy is not None and policy.enabled:
            policy.release()
    duration = time.perf_counter() - start
    return JobResult(
        index=index,
        success=error is None,
        duration=duration,
        error=error,
    )


def run_with_wavefront(
    config: BenchmarkConfig,
    job: Callable[[], None],
    policy: Optional[WavefrontPolicy] = None,
) -> List[JobResult]:
    """Run *config.total_jobs* instances of *job* respecting the wavefront policy."""
    results: List[JobResult] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config.concurrency
    ) as executor:
        futures = [
            executor.submit(_execute, job, i, policy)
            for i in range(config.total_jobs)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r.index)
    return results
