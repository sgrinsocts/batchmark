"""Runner that enforces a time budget across all jobs."""
from __future__ import annotations
import asyncio
from typing import Callable, List, Optional

from batchmark.budget import TimeBudget, check_budget
from batchmark.runner import JobResult, RunSummary, _run_job
from batchmark.config import BenchmarkConfig


async def run_with_budget(
    job: Callable,
    config: BenchmarkConfig,
    budget: Optional[TimeBudget] = None,
) -> RunSummary:
    """Run all jobs respecting concurrency and an optional time budget."""
    semaphore = asyncio.Semaphore(config.concurrency)
    results: List[JobResult] = []

    async def bounded(index: int) -> None:
        check_budget(budget, label=f"job-{index}")
        async with semaphore:
            check_budget(budget, label=f"job-{index}-acquired")
            result = await _run_job(job, index, config)
            results.append(result)

    tasks = [asyncio.create_task(bounded(i)) for i in range(config.total_jobs)]
    try:
        await asyncio.gather(*tasks)
    except RuntimeError:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    return RunSummary(results=results)
