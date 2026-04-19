"""Concurrency limiter using a semaphore for controlling parallel job execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable, List

from batchmark.runner import JobResult, RunSummary
from batchmark.config import BenchmarkConfig


@dataclass
class ConcurrencyLimiter:
    max_workers: int
    _semaphore: asyncio.Semaphore = field(init=False)

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self._semaphore = asyncio.Semaphore(self.max_workers)

    async def run(self, fn: Callable, *args, **kwargs):
        async with self._semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, fn, *args)


def make_concurrency_limiter(config: BenchmarkConfig) -> ConcurrencyLimiter:
    return ConcurrencyLimiter(max_workers=config.concurrency)


async def run_concurrently(
    jobs: List[Callable],
    config: BenchmarkConfig,
) -> RunSummary:
    import time

    limiter = make_concurrency_limiter(config)
    results: List[JobResult] = []

    async def _run(index: int, job: Callable) -> JobResult:
        start = time.perf_counter()
        try:
            await limiter.run(job)
            duration = time.perf_counter() - start
            return JobResult(index=index, success=True, duration=duration)
        except Exception as exc:
            duration = time.perf_counter() - start
            return JobResult(index=index, success=False, duration=duration, error=str(exc))

    tasks = [_run(i, job) for i, job in enumerate(jobs)]
    results = await asyncio.gather(*tasks)
    return RunSummary(results=list(results))
