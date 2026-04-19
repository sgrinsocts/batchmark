"""Runner that enforces a JobQuota across concurrent jobs."""
from __future__ import annotations
import concurrent.futures
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult, RunSummary
from batchmark.quota import JobQuota, check_quota, make_quota


def run_with_quota(
    job: Callable[[int], None],
    config: BenchmarkConfig,
    max_jobs: Optional[int] = None,
) -> RunSummary:
    """Run jobs respecting an optional quota cap."""
    quota: Optional[JobQuota] = make_quota(max_jobs)
    effective = config.job_count if quota is None else min(config.job_count, quota.max_jobs)

    results: List[JobResult] = []

    def _run(index: int) -> JobResult:
        import time
        start = time.perf_counter()
        try:
            job(index)
            duration = time.perf_counter() - start
            return JobResult(index=index, success=True, duration=duration)
        except Exception as exc:
            duration = time.perf_counter() - start
            return JobResult(index=index, success=False, duration=duration, error=str(exc))

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrency) as pool:
        futures = []
        for i in range(effective):
            check_quota(quota)
            futures.append(pool.submit(_run, i))
            if quota is not None:
                quota.increment()

        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r.index)
    return RunSummary(results=results)
