"""Runner that executes jobs with a hedged request policy."""
from __future__ import annotations

from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.hedge import HedgePolicy, run_with_hedge
from batchmark.runner import JobResult, RunSummary


def run_with_hedge_policy(
    jobs: List[Callable[[], JobResult]],
    config: BenchmarkConfig,
    policy: Optional[HedgePolicy] = None,
) -> RunSummary:
    """Execute each job, applying the hedge policy to every call."""
    results: List[JobResult] = []

    for idx, job in enumerate(jobs):
        def _bound(j: Callable[[], JobResult] = job) -> JobResult:
            return j()

        result = run_with_hedge(_bound, policy=policy)
        results.append(
            JobResult(
                index=idx,
                success=result.success,
                duration=result.duration,
                error=result.error,
            )
        )

    return RunSummary(results=results, config=config)
