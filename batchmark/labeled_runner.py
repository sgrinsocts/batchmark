"""Runner that executes jobs filtered or grouped by labels."""
from __future__ import annotations
from typing import Callable, Dict, List, Optional
from batchmark.labels import LabeledJob, filter_by_labels, group_by_label
from batchmark.runner import JobResult, run_all
from batchmark.config import BenchmarkConfig


def run_labeled(
    jobs: List[LabeledJob],
    config: BenchmarkConfig,
    selector: Optional[Dict[str, str]] = None,
) -> List[JobResult]:
    """Run jobs optionally filtered by a label selector."""
    selected = filter_by_labels(jobs, selector) if selector else jobs
    callables = [j.job for j in selected]
    return run_all(callables, config)


def run_by_label_group(
    jobs: List[LabeledJob],
    config: BenchmarkConfig,
    key: str,
) -> Dict[str, List[JobResult]]:
    """Run jobs grouped by a label key, returning results per group."""
    groups = group_by_label(jobs, key)
    return {
        group_value: run_all([j.job for j in group_jobs], config)
        for group_value, group_jobs in groups.items()
    }
