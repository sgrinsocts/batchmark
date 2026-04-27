"""Tests for batchmark.fanout module."""

from __future__ import annotations

import pytest

from batchmark.fanout import FanoutConfig, run_fanout
from batchmark.config import BenchmarkConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(**kwargs) -> BenchmarkConfig:
    return BenchmarkConfig(**kwargs)


def noop_job(value) -> None:
    """Job that succeeds for any input."""


def failing_job(value) -> None:
    """Job that always raises."""
    raise RuntimeError(f"boom: {value}")


def selective_failing_job(value) -> None:
    """Job that fails only for even inputs."""
    if value % 2 == 0:
        raise ValueError(f"even input: {value}")


# ---------------------------------------------------------------------------
# FanoutConfig validation
# ---------------------------------------------------------------------------

def test_fanout_config_defaults():
    cfg = FanoutConfig(inputs=[1, 2, 3])
    assert cfg.max_workers == 4
    assert cfg.fail_fast is False


def test_fanout_config_invalid_workers():
    with pytest.raises(ValueError, match="max_workers"):
        FanoutConfig(inputs=[], max_workers=0)


def test_fanout_config_invalid_inputs_type():
    with pytest.raises(TypeError, match="inputs"):
        FanoutConfig(inputs="not-a-list")


# ---------------------------------------------------------------------------
# run_fanout behaviour
# ---------------------------------------------------------------------------

def test_run_fanout_empty_inputs():
    cfg = FanoutConfig(inputs=[])
    summary = run_fanout(noop_job, cfg)
    assert summary.results == []


def test_run_fanout_all_succeed():
    cfg = FanoutConfig(inputs=[1, 2, 3, 4, 5], max_workers=2)
    summary = run_fanout(noop_job, cfg)
    assert len(summary.results) == 5
    assert all(r.success for r in summary.results)


def test_run_fanout_all_fail():
    cfg = FanoutConfig(inputs=["a", "b", "c"], max_workers=3)
    summary = run_fanout(failing_job, cfg)
    assert len(summary.results) == 3
    assert all(not r.success for r in summary.results)
    assert all("boom" in r.error for r in summary.results)


def test_run_fanout_results_sorted_by_index():
    cfg = FanoutConfig(inputs=list(range(10)), max_workers=4)
    summary = run_fanout(noop_job, cfg)
    indices = [r.index for r in summary.results]
    assert indices == sorted(indices)


def test_run_fanout_partial_failures():
    cfg = FanoutConfig(inputs=list(range(6)), max_workers=3)
    summary = run_fanout(selective_failing_job, cfg)
    succeeded = [r for r in summary.results if r.success]
    failed = [r for r in summary.results if not r.success]
    assert len(succeeded) == 3  # odd inputs: 1, 3, 5
    assert len(failed) == 3    # even inputs: 0, 2, 4


def test_run_fanout_fail_fast_stops_early():
    cfg = FanoutConfig(inputs=list(range(20)), max_workers=1, fail_fast=True)
    summary = run_fanout(failing_job, cfg)
    # With fail_fast=True and max_workers=1, should stop after first failure
    assert len(summary.results) < 20
    assert any(not r.success for r in summary.results)


def test_run_fanout_durations_non_negative():
    cfg = FanoutConfig(inputs=[10, 20, 30])
    summary = run_fanout(noop_job, cfg)
    assert all(r.duration >= 0.0 for r in summary.results)
