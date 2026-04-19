import pytest
from batchmark.tags import (
    TaggedJob,
    make_tagged_job,
    filter_by_tag,
    filter_by_any,
    filter_by_all,
    group_by_tag,
)
from batchmark.tagged_runner import run_tagged, run_by_tag_groups
from batchmark.config import BenchmarkConfig


def noop():
    return "ok"


def make_config():
    return BenchmarkConfig(concurrency=1, total_jobs=1)


def test_make_tagged_job():
    j = make_tagged_job(noop, ["fast", "smoke"])
    assert j.has_tag("fast")
    assert j.has_tag("smoke")
    assert not j.has_tag("slow")


def test_matches_any():
    j = make_tagged_job(noop, ["a", "b"])
    assert j.matches_any(["b", "c"])
    assert not j.matches_any(["x", "y"])


def test_matches_all():
    j = make_tagged_job(noop, ["a", "b"])
    assert j.matches_all(["a", "b"])
    assert not j.matches_all(["a", "c"])


def test_filter_by_tag():
    jobs = [make_tagged_job(noop, ["fast"]), make_tagged_job(noop, ["slow"])]
    result = filter_by_tag(jobs, "fast")
    assert len(result) == 1
    assert result[0].has_tag("fast")


def test_filter_by_any():
    jobs = [
        make_tagged_job(noop, ["a"]),
        make_tagged_job(noop, ["b"]),
        make_tagged_job(noop, ["c"]),
    ]
    result = filter_by_any(jobs, ["a", "c"])
    assert len(result) == 2


def test_filter_by_all():
    jobs = [
        make_tagged_job(noop, ["a", "b"]),
        make_tagged_job(noop, ["a"]),
    ]
    result = filter_by_all(jobs, ["a", "b"])
    assert len(result) == 1


def test_group_by_tag():
    jobs = [
        make_tagged_job(noop, ["fast", "smoke"]),
        make_tagged_job(noop, ["slow"]),
        make_tagged_job(noop, ["smoke"]),
    ]
    groups = group_by_tag(jobs)
    assert len(groups["smoke"]) == 2
    assert len(groups["fast"]) == 1
    assert len(groups["slow"]) == 1


def test_run_tagged_no_filter():
    jobs = [make_tagged_job(noop, ["x"]) for _ in range(3)]
    cfg = BenchmarkConfig(concurrency=1, total_jobs=3)
    results = run_tagged(jobs, cfg)
    assert len(results) == 3


def test_run_tagged_with_require_tag():
    jobs = [
        make_tagged_job(noop, ["smoke"]),
        make_tagged_job(noop, ["slow"]),
        make_tagged_job(noop, ["smoke"]),
    ]
    cfg = BenchmarkConfig(concurrency=1, total_jobs=2)
    results = run_tagged(jobs, cfg, require_tag="smoke")
    assert len(results) == 2


def test_run_by_tag_groups_keys():
    jobs = [
        make_tagged_job(noop, ["a"]),
        make_tagged_job(noop, ["b"]),
    ]
    cfg = BenchmarkConfig(concurrency=1, total_jobs=1)
    groups = run_by_tag_groups(jobs, cfg)
    assert "a" in groups
    assert "b" in groups
