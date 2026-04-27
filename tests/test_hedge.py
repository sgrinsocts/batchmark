"""Tests for batchmark.hedge module."""
from __future__ import annotations

import time
import pytest

from batchmark.runner import JobResult
from batchmark.hedge import (
    HedgePolicy,
    make_hedge_policy,
    run_with_hedge,
    describe_hedge_policy,
)


def make_result(success: bool = True, duration: float = 0.01) -> JobResult:
    return JobResult(index=0, success=success, duration=duration, error=None)


def test_default_policy_disabled():
    p = HedgePolicy()
    assert p.enabled is False


def test_policy_enabled_when_flag_set():
    p = make_hedge_policy(delay_seconds=0.1, enabled=True)
    assert p.enabled is True
    assert p.should_hedge() is True


def test_policy_invalid_negative_delay():
    with pytest.raises(ValueError, match="delay_seconds"):
        HedgePolicy(delay_seconds=-1.0, enabled=True)


def test_policy_invalid_max_hedges():
    with pytest.raises(ValueError, match="max_hedges"):
        HedgePolicy(max_hedges=0)


def test_run_without_policy_calls_job():
    called = []

    def job() -> JobResult:
        called.append(1)
        return make_result()

    result = run_with_hedge(job, policy=None)
    assert result.success is True
    assert len(called) == 1


def test_run_disabled_policy_calls_job_once():
    called = []

    def job() -> JobResult:
        called.append(1)
        return make_result()

    policy = HedgePolicy(enabled=False)
    result = run_with_hedge(job, policy=policy)
    assert result.success is True
    assert len(called) == 1


def test_run_with_hedge_returns_success():
    def job() -> JobResult:
        return make_result(success=True)

    policy = make_hedge_policy(delay_seconds=0.0, enabled=True)
    result = run_with_hedge(job, policy=policy)
    assert result.success is True


def test_run_hedge_prefers_successful_result():
    attempts = []

    def job() -> JobResult:
        attempts.append(1)
        return make_result(success=True)

    policy = make_hedge_policy(delay_seconds=0.0, enabled=True)
    result = run_with_hedge(job, policy=policy)
    assert result.success is True


def test_describe_disabled():
    p = HedgePolicy()
    assert "disabled" in describe_hedge_policy(p)


def test_describe_enabled():
    p = make_hedge_policy(delay_seconds=0.2, max_hedges=2, enabled=True)
    desc = describe_hedge_policy(p)
    assert "enabled" in desc
    assert "0.2" in desc
    assert "2" in desc
