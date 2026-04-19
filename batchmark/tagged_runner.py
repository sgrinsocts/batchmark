from __future__ import annotations
from typing import Callable, Iterable
from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult, run_all
from batchmark.tags import TaggedJob, filter_by_tag, filter_by_any, filter_by_all


def run_tagged(
    jobs: Iterable[TaggedJob],
    config: BenchmarkConfig,
    *,
    require_tag: str | None = None,
    any_tags: Iterable[str] | None = None,
    all_tags: Iterable[str] | None = None,
) -> list[JobResult]:
    """Run jobs filtered by tag criteria."""
    job_list = list(jobs)

    if require_tag is not None:
        job_list = filter_by_tag(job_list, require_tag)
    if any_tags is not None:
        job_list = filter_by_any(job_list, any_tags)
    if all_tags is not None:
        job_list = filter_by_all(job_list, all_tags)

    callables: list[Callable] = [j.job for j in job_list]
    return run_all(callables, config)


def run_by_tag_groups(
    jobs: Iterable[TaggedJob],
    config: BenchmarkConfig,
) -> dict[str, list[JobResult]]:
    """Run each tag group independently and return results per tag."""
    from batchmark.tags import group_by_tag

    groups = group_by_tag(list(jobs))
    return {
        tag: run_all([j.job for j in group], config)
        for tag, group in groups.items()
    }
