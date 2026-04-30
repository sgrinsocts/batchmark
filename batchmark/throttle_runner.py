"""Runner that applies a RateLimiter to each job before execution."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult
from batchmark.throttle import RateLimiter, make_rate_limiter
from batchmark.throttle_config import ThrottleConfig


def _execute(
    index: int,
    job: Callable[[], None],
    limiter: RateLimiter,
) -> JobResult:
    limiter()          # blocks until the rate limit allows
    start = time.perf_counter()
    error: Optional[str] = None
    try:
        job()
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
    duration = time.perf_counter() - start
    return JobResult(index=index, duration=duration, error=error)


def run_with_throttle(
    config: BenchmarkConfig,
    job: Callable[[], None],
    throttle: Optional[ThrottleConfig] = None,
) -> List[JobResult]:
    """Run *config.num_jobs* calls to *job* subject to optional rate limiting."""
    if throttle is not None and throttle.is_active():
        limiter = throttle.to_limiter()
    else:
        limiter = make_rate_limiter(0.0)

    results: List[JobResult] = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as pool:
        futures = [
            pool.submit(_execute, i, job, limiter)
            for i in range(config.num_jobs)
        ]
        for fut in futures:
            results.append(fut.result())
    results.sort(key=lambda r: r.index)
    return results
