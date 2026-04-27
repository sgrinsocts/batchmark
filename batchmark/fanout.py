"""Fanout runner: broadcast a single job function to multiple input sets concurrently."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from batchmark.runner import JobResult, RunSummary
from batchmark.config import BenchmarkConfig


@dataclass
class FanoutConfig:
    """Configuration for fanout execution."""
    inputs: List[Any] = field(default_factory=list)
    max_workers: int = 4
    fail_fast: bool = False

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if not isinstance(self.inputs, list):
            raise TypeError("inputs must be a list")


def _execute_one(
    job: Callable[[Any], Any],
    input_value: Any,
    index: int,
) -> JobResult:
    """Run job with a single input and return a JobResult."""
    start = time.perf_counter()
    try:
        job(input_value)
        duration = time.perf_counter() - start
        return JobResult(index=index, success=True, duration=duration, error=None)
    except Exception as exc:  # noqa: BLE001
        duration = time.perf_counter() - start
        return JobResult(index=index, success=False, duration=duration, error=str(exc))


def run_fanout(
    job: Callable[[Any], Any],
    fanout_cfg: FanoutConfig,
    cfg: Optional[BenchmarkConfig] = None,
) -> RunSummary:
    """Broadcast *job* across all inputs in *fanout_cfg*, respecting concurrency."""
    results: List[JobResult] = []
    inputs = fanout_cfg.inputs

    if not inputs:
        return RunSummary(results=results)

    workers = min(fanout_cfg.max_workers, len(inputs))
    aborted = False

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_execute_one, job, inp, idx): idx
            for idx, inp in enumerate(inputs)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if fanout_cfg.fail_fast and not result.success:
                aborted = True
                for pending in futures:
                    pending.cancel()
                break

    results.sort(key=lambda r: r.index)
    return RunSummary(results=results)
