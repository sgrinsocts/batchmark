"""Runner that enforces per-job timeouts and records results."""
from __future__ import annotations

import time
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult
from batchmark.timeout import TimeoutPolicy, run_with_timeout


def run_with_timeout_policy(
    config: BenchmarkConfig,
    job: Callable[[int], None],
    policy: TimeoutPolicy,
    indices: Optional[List[int]] = None,
) -> List[JobResult]:
    """Run *job* for each index, enforcing *policy* per call.

    Jobs that exceed the timeout are recorded as failures with the
    TimeoutError message; all other exceptions are also caught.
    """
    if indices is None:
        indices = list(range(config.num_jobs))

    results: List[JobResult] = []
    for idx in indices:
        start = time.perf_counter()
        error: Optional[str] = None
        try:
            run_with_timeout(job, policy, idx)
        except TimeoutError as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
        duration = time.perf_counter() - start
        results.append(JobResult(index=idx, duration=duration, error=error))

    return results
