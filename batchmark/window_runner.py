"""Runner that enforces a sliding window rate limit across jobs."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult
from batchmark.window import WindowPolicy


def _execute(
    job: Callable[[], None],
    index: int,
    policy: WindowPolicy,
) -> JobResult:
    policy.acquire()
    start = __import__("time").monotonic()
    try:
        job()
        duration = __import__("time").monotonic() - start
        return JobResult(index=index, success=True, duration=duration)
    except Exception as exc:  # noqa: BLE001
        duration = __import__("time").monotonic() - start
        return JobResult(
            index=index, success=False, duration=duration, error=str(exc)
        )


def run_with_window(
    jobs: List[Callable[[], None]],
    config: BenchmarkConfig,
    policy: Optional[WindowPolicy] = None,
) -> List[JobResult]:
    """Run *jobs* concurrently, each acquiring a window slot before starting."""
    if policy is None:
        policy = WindowPolicy()  # unlimited

    results: List[JobResult] = []
    workers = max(1, config.concurrency)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_execute, job, idx, policy): idx
            for idx, job in enumerate(jobs)
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.index)
    return results
