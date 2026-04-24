"""Tests for batchmark.drain."""

from __future__ import annotations

import time
import pytest

from batchmark.drain import DrainPolicy, make_drain_policy, describe_drain_policy


# ---------------------------------------------------------------------------
# Construction & validation
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    policy = DrainPolicy()
    assert policy.enabled is False
    assert policy.timeout_seconds == 30.0
    assert policy.poll_interval == 0.1


def test_policy_enabled_when_flag_set():
    policy = DrainPolicy(enabled=True)
    assert policy.enabled is True


def test_invalid_negative_timeout_raises():
    with pytest.raises(ValueError, match="timeout_seconds"):
        DrainPolicy(timeout_seconds=-1.0)


def test_invalid_zero_poll_interval_raises():
    with pytest.raises(ValueError, match="poll_interval"):
        DrainPolicy(poll_interval=0.0)


def test_invalid_negative_poll_interval_raises():
    with pytest.raises(ValueError, match="poll_interval"):
        DrainPolicy(poll_interval=-0.5)


# ---------------------------------------------------------------------------
# make_drain_policy helper
# ---------------------------------------------------------------------------

def test_make_drain_policy_returns_instance():
    policy = make_drain_policy(enabled=True, timeout_seconds=5.0)
    assert isinstance(policy, DrainPolicy)
    assert policy.enabled is True
    assert policy.timeout_seconds == 5.0


def test_make_drain_policy_invalid_raises():
    with pytest.raises(ValueError):
        make_drain_policy(timeout_seconds=-1.0)


# ---------------------------------------------------------------------------
# wait_for_drain behaviour
# ---------------------------------------------------------------------------

def test_disabled_policy_returns_true_immediately():
    policy = DrainPolicy(enabled=False)
    # Even if queue is never empty, disabled policy should return True instantly
    result = policy.wait_for_drain(lambda: False)
    assert result is True


def test_drains_cleanly_when_queue_empties():
    policy = DrainPolicy(enabled=True, timeout_seconds=2.0, poll_interval=0.01)
    calls = [0]

    def is_empty():
        calls[0] += 1
        return calls[0] >= 3  # empty after a couple of polls

    result = policy.wait_for_drain(is_empty)
    assert result is True


def test_returns_false_on_timeout():
    policy = DrainPolicy(enabled=True, timeout_seconds=0.05, poll_interval=0.01)
    result = policy.wait_for_drain(lambda: False)  # never empties
    assert result is False


def test_on_timeout_callback_called():
    policy = DrainPolicy(enabled=True, timeout_seconds=0.05, poll_interval=0.01)
    triggered = []
    policy.wait_for_drain(lambda: False, on_timeout=lambda: triggered.append(1))
    assert triggered == [1]


def test_on_timeout_not_called_when_drains_cleanly():
    policy = DrainPolicy(enabled=True, timeout_seconds=2.0, poll_interval=0.01)
    triggered = []
    policy.wait_for_drain(lambda: True, on_timeout=lambda: triggered.append(1))
    assert triggered == []


# ---------------------------------------------------------------------------
# describe_drain_policy
# ---------------------------------------------------------------------------

def test_describe_disabled():
    policy = DrainPolicy(enabled=False)
    assert describe_drain_policy(policy) == "drain: disabled"


def test_describe_enabled_contains_fields():
    policy = DrainPolicy(enabled=True, timeout_seconds=10.0, poll_interval=0.2)
    desc = describe_drain_policy(policy)
    assert "enabled" in desc
    assert "10.0" in desc
    assert "0.2" in desc
