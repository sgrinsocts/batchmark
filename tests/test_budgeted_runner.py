"""Tests for batchmark.budgeted_runner."""
import asyncio
import pytest
from batchmark.budgeted_runner import run_with_budget
from batchmark.budget import TimeBudget
from batchmark.config import BenchmarkConfig


def make_config(**kwargs) -> BenchmarkConfig:
    defaults = dict(total_jobs=4, concurrency=2, timeout=5.0)
    defaults.update(kwargs)
    return BenchmarkConfig(**defaults)


async def noop_job(index: int) -> str:
    return f"ok-{index}"


def test_run_with_no_budget_succeeds():
    config = make_config(total_jobs=3)
    summary = asyncio.run(run_with_budget(noop_job, config, budget=None))
    assert len(summary.results) == 3
    assert all(r.success for r in summary.results)


def test_run_with_ample_budget_succeeds():
    config = make_config(total_jobs=3)
    budget = TimeBudget(max_seconds=10.0)
    summary = asyncio.run(run_with_budget(noop_job, config, budget=budget))
    assert len(summary.results) == 3


def test_run_with_expired_budget_raises():
    import time
    config = make_config(total_jobs=5)
    budget = TimeBudget(max_seconds=0.001)
    time.sleep(0.05)  # expire budget before run
    with pytest.raises(RuntimeError, match="Time budget exceeded"):
        asyncio.run(run_with_budget(noop_job, config, budget=budget))
