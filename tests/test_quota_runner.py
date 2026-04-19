"""Tests for batchmark.quota_runner."""
import pytest
from batchmark.config import BenchmarkConfig
from batchmark.quota_runner import run_with_quota


def make_config(job_count: int = 6, concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(job_count=job_count, concurrency=concurrency)


def noop_job(index: int) -> None:
    pass


def failing_job(index: int) -> None:
    raise ValueError(f"fail {index}")


def test_run_no_quota_runs_all():
    cfg = make_config(job_count=4)
    summary = run_with_quota(noop_job, cfg, max_jobs=None)
    assert len(summary.results) == 4
    assert all(r.success for r in summary.results)


def test_run_quota_limits_jobs():
    cfg = make_config(job_count=10)
    summary = run_with_quota(noop_job, cfg, max_jobs=3)
    assert len(summary.results) == 3


def test_run_quota_larger_than_job_count():
    cfg = make_config(job_count=4)
    summary = run_with_quota(noop_job, cfg, max_jobs=100)
    assert len(summary.results) == 4


def test_run_with_failures():
    cfg = make_config(job_count=4)
    summary = run_with_quota(failing_job, cfg, max_jobs=None)
    assert all(not r.success for r in summary.results)
    assert all("fail" in (r.error or "") for r in summary.results)


def test_results_sorted_by_index():
    cfg = make_config(job_count=5, concurrency=5)
    summary = run_with_quota(noop_job, cfg, max_jobs=None)
    indices = [r.index for r in summary.results]
    assert indices == sorted(indices)
