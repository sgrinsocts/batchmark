"""Tests for batchmark.jitter."""

from __future__ import annotations

import pytest

from batchmark.jitter import JitterPolicy, describe_jitter_policy, make_jitter_policy


def test_default_policy_disabled():
    policy = JitterPolicy()
    assert not policy.enabled()


def test_policy_enabled_when_strategy_set():
    policy = JitterPolicy(strategy="full", max_seconds=0.5)
    assert policy.enabled()


def test_policy_invalid_strategy():
    with pytest.raises(ValueError, match="Unknown jitter strategy"):
        JitterPolicy(strategy="random")  # type: ignore[arg-type]


def test_policy_invalid_negative_max():
    with pytest.raises(ValueError, match="max_seconds"):
        JitterPolicy(strategy="full", max_seconds=-1.0)


def test_apply_none_strategy_returns_base():
    policy = JitterPolicy(strategy="none", max_seconds=2.0)
    assert policy.apply(1.0) == 1.0


def test_apply_full_jitter_within_range():
    policy = JitterPolicy(strategy="full", max_seconds=1.0, seed=42)
    for _ in range(20):
        result = policy.apply(base_delay=1.0)
        assert 0.0 <= result <= 1.0


def test_apply_equal_jitter_within_range():
    policy = JitterPolicy(strategy="equal", max_seconds=2.0, seed=0)
    for _ in range(20):
        result = policy.apply(base_delay=2.0)
        assert 0.0 <= result <= 2.0


def test_apply_decorrelated_uses_prev_delay():
    policy = JitterPolicy(strategy="decorrelated", max_seconds=5.0, seed=7)
    result = policy.apply(base_delay=1.0, prev_delay=1.0)
    assert 0.0 <= result <= 5.0


def test_apply_decorrelated_no_prev_uses_base():
    policy = JitterPolicy(strategy="decorrelated", max_seconds=5.0, seed=3)
    result = policy.apply(base_delay=1.0)
    assert 0.0 <= result <= 5.0


def test_make_jitter_policy_returns_instance():
    policy = make_jitter_policy(strategy="equal", max_seconds=0.5)
    assert isinstance(policy, JitterPolicy)
    assert policy.strategy == "equal"


def test_describe_disabled():
    policy = JitterPolicy()
    assert "disabled" in describe_jitter_policy(policy)


def test_describe_enabled():
    policy = JitterPolicy(strategy="full", max_seconds=0.3)
    desc = describe_jitter_policy(policy)
    assert "full" in desc
    assert "0.3" in desc
