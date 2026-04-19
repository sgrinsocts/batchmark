"""Tests for ConcurrencyLimiter and run_concurrently."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import MagicMock

from batchmark.concurrency import ConcurrencyLimiter, make_concurrency_limiter, run_concurrently
from batchmark.config import BenchmarkConfig


def make_config(concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(concurrency=concurrency, jobs=[], output="text")


def noop():
    pass


def failing_job():
    raise RuntimeError("boom")


def test_limiter_invalid_workers():
    with pytest.raises(ValueError, match="max_workers"):
        ConcurrencyLimiter(max_workers=0)


def test_make_concurrency_limiter():
    cfg = make_config(concurrency=3)
    limiter = make_concurrency_limiter(cfg)
    assert limiter.max_workers == 3


def test_run_concurrently_all_succeed():
    cfg = make_config(concurrency=2)
    jobs = [noop] * 5
    summary = asyncio.run(run_concurrently(jobs, cfg))
    assert len(summary.results) == 5
    assert all(r.success for r in summary.results)


def test_run_concurrently_with_failure():
    cfg = make_config(concurrency=2)
    jobs = [noop, failing_job, noop]
    summary = asyncio.run(run_concurrently(jobs, cfg))
    successes = [r for r in summary.results if r.success]
    failures = [r for r in summary.results if not r.success]
    assert len(successes) == 2
    assert len(failures) == 1
    assert "boom" in failures[0].error


def test_run_concurrently_empty():
    cfg = make_config(concurrency=2)
    summary = asyncio.run(run_concurrently([], cfg))
    assert summary.results == []


def test_run_concurrently_indices():
    cfg = make_config(concurrency=2)
    jobs = [noop] * 4
    summary = asyncio.run(run_concurrently(jobs, cfg))
    indices = sorted(r.index for r in summary.results)
    assert indices == [0, 1, 2, 3]
