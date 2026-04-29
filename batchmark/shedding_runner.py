"""Runner that applies load-shedding before executing jobs."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult, RunSummary
from batchmark.shedding import SheddingPolicy


def _execute(
    job: Callable[[], None],
    index: int,
) -> JobResult:
    import time
    start = time.perf_counter()
    try:
        job()
        return JobResult(index=index, success=True, duration=time.perf_counter() - start)
    except Exception as exc:  # noqa: BLE001
        return JobResult(index=index, success=False, duration=time.perf_counter() - start, error=str(exc))


def run_with_shedding(
    jobs: List[Callable[[], None]],
    config: BenchmarkConfig,
    policy: Optional[SheddingPolicy] = None,
) -> RunSummary:
    """Run jobs, dropping any that the shedding policy rejects.

    Shed jobs are recorded as failures with error='shed'.
    """
    results: List[JobResult] = []
    accepted: List[tuple[int, Callable[[], None]]] = []

    queue_depth = 0
    capacity = max(config.concurrency, 1)

    for idx, job in enumerate(jobs):
        if policy and policy.should_shed(queue_depth=queue_depth, capacity=capacity):
            import time
            results.append(
                JobResult(index=idx, success=False, duration=0.0, error="shed")
            )
        else:
            if policy:
                policy.record_submission()
            accepted.append((idx, job))
            queue_depth += 1

    with ThreadPoolExecutor(max_workers=config.concurrency) as pool:
        futures = {pool.submit(_execute, job, idx): idx for idx, job in accepted}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.index)
    shed_count = sum(1 for r in results if r.error == "shed")
    return RunSummary(results=results, shed_count=shed_count)
