"""Tests for batchmark.wavefront_runner."""

from __future__ import annotations

import time
from typing import List

import pytest

from batchmark.config import BenchmarkConfig
from batchmark.wavefront import WavefrontPolicy
from batchmark.wavefront_runner import run_with_wavefront


def make_config(total_jobs: int = 4, concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(total_jobs=total_jobs, concurrency=concurrency)


def noop_job() -> None:
    pass


def failing_job() -> None:
    raise RuntimeError("boom")


def test_run_no_policy_all_succeed():
    cfg = make_config(total_jobs=5)
    results = run_with_wavefront(cfg, noop_job, policy=None)
    assert len(results) == 5
    assert all(r.success for r in results)


def test_run_with_unlimited_policy_all_succeed():
    cfg = make_config(total_jobs=4)
    policy = WavefrontPolicy(max_in_flight=0)
    results = run_with_wavefront(cfg, noop_job, policy=policy)
    assert all(r.success for r in results)


def test_run_with_limited_policy_all_succeed_eventually():
    cfg = make_config(total_jobs=6, concurrency=3)
    policy = WavefrontPolicy(max_in_flight=2, acquire_timeout=5.0)
    results = run_with_wavefront(cfg, noop_job, policy=policy)
    assert len(results) == 6
    assert all(r.success for r in results)


def test_run_failing_jobs_captured():
    cfg = make_config(total_jobs=3)
    results = run_with_wavefront(cfg, failing_job, policy=None)
    assert all(not r.success for r in results)
    assert all("boom" in (r.error or "") for r in results)


def test_run_results_sorted_by_index():
    cfg = make_config(total_jobs=8, concurrency=4)
    results = run_with_wavefront(cfg, noop_job, policy=None)
    indices = [r.index for r in results]
    assert indices == sorted(indices)


def test_run_timeout_policy_records_failure():
    """When the semaphore is saturated and timeout is tiny, jobs should fail gracefully."""
    cfg = make_config(total_jobs=4, concurrency=4)
    # Only 1 slot, very short timeout — most jobs will fail to acquire
    policy = WavefrontPolicy(max_in_flight=1, acquire_timeout=0.001)

    slow_job_called = []

    def slow_job() -> None:
        slow_job_called.append(1)
        time.sleep(0.5)

    results = run_with_wavefront(cfg, slow_job, policy=policy)
    assert len(results) == 4
    failures = [r for r in results if not r.success]
    # At least some should fail due to timeout
    assert len(failures) >= 1
    for f in failures:
        assert "timeout" in (f.error or "")
