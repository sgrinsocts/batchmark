"""Tests for batchmark.deadline."""

from __future__ import annotations

import time

import pytest

from batchmark.deadline import (
    DeadlinePolicy,
    describe_deadline_policy,
    make_deadline_policy,
    run_with_deadline,
)


def test_policy_defaults() -> None:
    p = DeadlinePolicy()
    assert p.seconds == 0.0
    assert p.grace_period == 0.0
    assert not p.enabled


def test_policy_enabled_when_seconds_positive() -> None:
    p = DeadlinePolicy(seconds=5.0)
    assert p.enabled


def test_policy_invalid_negative_seconds() -> None:
    with pytest.raises(ValueError, match="seconds"):
        DeadlinePolicy(seconds=-1.0)


def test_policy_invalid_negative_grace() -> None:
    with pytest.raises(ValueError, match="grace_period"):
        DeadlinePolicy(seconds=1.0, grace_period=-0.1)


def test_deadline_at_returns_none_when_disabled() -> None:
    p = DeadlinePolicy()
    assert p.deadline_at() is None


def test_deadline_at_returns_future_timestamp() -> None:
    p = DeadlinePolicy(seconds=10.0)
    now = time.monotonic()
    dl = p.deadline_at(now)
    assert dl is not None
    assert dl > now


def test_make_deadline_policy_returns_instance() -> None:
    p = make_deadline_policy(seconds=2.0, grace_period=0.5)
    assert isinstance(p, DeadlinePolicy)
    assert p.seconds == 2.0
    assert p.grace_period == 0.5


def test_no_deadline_runs_normally() -> None:
    p = DeadlinePolicy()
    called = []
    run_with_deadline(lambda: called.append(1), p)
    assert called == [1]


def test_run_within_deadline_succeeds() -> None:
    p = DeadlinePolicy(seconds=5.0)
    result = run_with_deadline(lambda: 42, p)
    assert result == 42


def test_run_exceeds_deadline_raises() -> None:
    # Force the deadline to be in the past by using a tiny seconds value
    # and a job that sleeps longer.
    p = DeadlinePolicy(seconds=0.001)
    with pytest.raises(RuntimeError, match="Deadline exceeded"):
        run_with_deadline(lambda: time.sleep(0.05), p)


def test_describe_disabled_policy() -> None:
    p = DeadlinePolicy()
    assert describe_deadline_policy(p) == "deadline: none"


def test_describe_enabled_policy() -> None:
    p = DeadlinePolicy(seconds=3.0)
    desc = describe_deadline_policy(p)
    assert "3.0" in desc


def test_describe_policy_with_grace() -> None:
    p = DeadlinePolicy(seconds=3.0, grace_period=0.5)
    desc = describe_deadline_policy(p)
    assert "grace" in desc
    assert "0.5" in desc
