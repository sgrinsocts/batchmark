"""Tests for run_with_throttle."""
from __future__ import annotations

import time
import pytest

from batchmark.config import BenchmarkConfig
from batchmark.throttle_config import ThrottleConfig
from batchmark.throttle_runner import run_with_throttle


def make_config(num_jobs: int = 4, concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(num_jobs=num_jobs, concurrency=concurrency)


def noop_job() -> None:
    pass


def failing_job() -> None:
    raise RuntimeError("boom")


def test_run_no_throttle_all_succeed():
    results = run_with_throttle(make_config(4), noop_job)
    assert len(results) == 4
    assert all(r.error is None for r in results)


def test_run_no_throttle_failures_captured():
    results = run_with_throttle(make_config(3), failing_job)
    assert all(r.error == "boom" for r in results)


def test_run_with_disabled_throttle_runs_all():
    cfg = ThrottleConfig(enabled=False, rate=100.0)
    results = run_with_throttle(make_config(4), noop_job, throttle=cfg)
    assert len(results) == 4


def test_run_with_active_throttle_runs_all():
    # High rate so the test stays fast
    cfg = ThrottleConfig(enabled=True, rate=1000.0)
    results = run_with_throttle(make_config(4), noop_job, throttle=cfg)
    assert len(results) == 4
    assert all(r.error is None for r in results)


def test_results_sorted_by_index():
    results = run_with_throttle(make_config(6), noop_job)
    indices = [r.index for r in results]
    assert indices == sorted(indices)


def test_results_have_positive_duration():
    results = run_with_throttle(make_config(3), noop_job)
    assert all(r.duration >= 0 for r in results)


def test_throttle_slows_execution():
    """With rate=2 and 4 serial jobs the wall time should be >= ~1.5 s."""
    cfg = ThrottleConfig(enabled=True, rate=2.0)
    # Use concurrency=1 to force sequential execution through the limiter
    config = BenchmarkConfig(num_jobs=4, concurrency=1)
    start = time.perf_counter()
    run_with_throttle(config, noop_job, throttle=cfg)
    elapsed = time.perf_counter() - start
    # 4 calls at 2/s → at least 1.5 s gap between first and last acquire
    assert elapsed >= 1.4
