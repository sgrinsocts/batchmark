"""Runner wrapper that integrates caching and retry for batch jobs."""
from __future__ import annotations
import time
from typing import Callable, Any

from batchmark.cache import ResultCache
from batchmark.retry import RetryPolicy, with_retry
from batchmark.runner import JobResult


def run_with_cache_and_retry(
    job_fn: Callable[[Any], Any],
    payload: Any,
    cache: ResultCache,
    policy: RetryPolicy,
    job_id: str = "",
) -> JobResult:
    """Execute job_fn(payload) with cache lookup and retry on failure."""
    hit, cached_value = cache.get(payload)
    if hit:
        return JobResult(
            job_id=job_id,
            success=True,
            duration=0.0,
            result=cached_value,
            error=None,
            cached=True,
        )

    start = time.perf_counter()
    try:
        result = with_retry(job_fn, policy, payload)
        duration = time.perf_counter() - start
        cache.set(payload, result)
        return JobResult(
            job_id=job_id,
            success=True,
            duration=duration,
            result=result,
            error=None,
            cached=False,
        )
    except Exception as exc:
        duration = time.perf_counter() - start
        return JobResult(
            job_id=job_id,
            success=False,
            duration=duration,
            result=None,
            error=str(exc),
            cached=False,
        )
