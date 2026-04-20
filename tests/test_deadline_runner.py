"""Tests for batchmark.deadline_runner."""

from __future__ import annotations

import time
from typing import List

import pytest

from batchmark.config import BenchmarkConfig
from batchmark.deadline import DeadlinePolicy
from batchmark.deadline_runner import run_with_deadline_policy
from batchmark.runner import RunSummary


def make_config(concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(concurrency=concurrency, job_count=0)


def noop_job() -> str:
    return "ok"


def slow_job() -> None:
    time.sleep(0.05)


def failing_job() -> None:
    raise ValueError("boom")


def test_run_no_policy_all_succeed() -> None:
    jobs = [noop_job] * 4
    summary = run_with_deadline_policy(jobs, make_config())
    assert isinstance(summary, RunSummary)
    assert len(summary.results) == 4
    assert all(r.success for r in summary.results)


def test_run_with_ample_deadline_all_succeed() -> None:
    policy = DeadlinePolicy(seconds=10.0)
    jobs = [noop_job] * 3
    summary = run_with_deadline_policy(jobs, make_config(), policy)
    assert all(r.success for r in summary.results)


def test_run_with_tight_deadline_marks_failure() -> None:
    policy = DeadlinePolicy(seconds=0.001)
    jobs = [slow_job] * 2
    summary = run_with_deadline_policy(jobs, make_config(concurrency=1), policy)
    # At least one job should fail due to deadline
    assert any(not r.success for r in summary.results)


def test_run_failing_job_captured() -> None:
    policy = DeadlinePolicy(seconds=5.0)
    jobs = [failing_job, noop_job]
    summary = run_with_deadline_policy(jobs, make_config(), policy)
    failures = [r for r in summary.results if not r.success]
    assert len(failures) == 1
    assert "boom" in (failures[0].error or "")


def test_results_sorted_by_index() -> None:
    jobs = [noop_job] * 5
    summary = run_with_deadline_policy(jobs, make_config(concurrency=5))
    indices = [r.index for r in summary.results]
    assert indices == sorted(indices)


def test_empty_jobs_returns_empty_summary() -> None:
    summary = run_with_deadline_policy([], make_config())
    assert summary.results == []
