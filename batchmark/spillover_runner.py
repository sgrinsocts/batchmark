"""Runner that redirects excess jobs to a secondary callable based on a SpilloverPolicy."""

from __future__ import annotations

from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult, RunSummary, _run_job
from batchmark.spillover import SpilloverPolicy


def _execute(
    index: int,
    job: Callable,
    config: BenchmarkConfig,
    policy: SpilloverPolicy,
    secondary: Optional[Callable],
) -> tuple[JobResult, bool]:
    """Run a single job, routing to secondary if spillover should occur.

    Returns (result, was_spilled).
    """
    if policy.should_spill() and secondary is not None:
        policy.record_spill()
        result = _run_job(index, secondary, config)
        return result, True
    policy.record_primary()
    result = _run_job(index, job, config)
    return result, False


def run_with_spillover(
    jobs: List[Callable],
    config: BenchmarkConfig,
    policy: Optional[SpilloverPolicy] = None,
    secondary: Optional[Callable] = None,
) -> RunSummary:
    """Run jobs with optional spillover to a secondary callable.

    When the policy triggers, excess jobs are handed off to *secondary*.
    If *secondary* is None, spilled jobs still run the original job callable.
    """
    if policy is None or not policy.enabled:
        results = [_run_job(i, job, config) for i, job in enumerate(jobs)]
        return RunSummary(results=results)

    results: List[JobResult] = []
    for i, job in enumerate(jobs):
        result, _ = _execute(i, job, config, policy, secondary)
        results.append(result)

    return RunSummary(results=results)
