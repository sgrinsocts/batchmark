"""Batch job runner with configurable concurrency."""

import time
import concurrent.futures
from dataclasses import dataclass, field
from typing import Callable, List, Any

from batchmark.config import BenchmarkConfig


@dataclass
class JobResult:
    job_id: int
    success: bool
    duration: float
    error: str = ""
    output: Any = None


@dataclass
class RunSummary:
    total: int
    succeeded: int
    failed: int
    total_duration: float
    results: List[JobResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.succeeded / self.total if self.total else 0.0

    @property
    def avg_duration(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.duration for r in self.results) / len(self.results)


def _run_job(job_fn: Callable, job_id: int, *args, **kwargs) -> JobResult:
    start = time.perf_counter()
    try:
        output = job_fn(*args, **kwargs)
        duration = time.perf_counter() - start
        return JobResult(job_id=job_id, success=True, duration=duration, output=output)
    except Exception as exc:
        duration = time.perf_counter() - start
        return JobResult(job_id=job_id, success=False, duration=duration, error=str(exc))


def run_benchmark(job_fn: Callable, config: BenchmarkConfig, jobs: List[Any] = None) -> RunSummary:
    """Run benchmark jobs according to config."""
    num_jobs = config.num_jobs
    job_args = jobs if jobs is not None else [None] * num_jobs
    results: List[JobResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = {
            executor.submit(_run_job, job_fn, idx, arg): idx
            for idx, arg in enumerate(job_args)
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.job_id)
    succeeded = sum(1 for r in results if r.success)
    total_duration = sum(r.duration for r in results)

    return RunSummary(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        total_duration=total_duration,
        results=results,
    )
