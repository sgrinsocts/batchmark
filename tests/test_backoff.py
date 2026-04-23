"""Tests for batchmark.backoff."""

import pytest

from batchmark.backoff import (
    BackoffPolicy,
    describe_backoff_policy,
    make_backoff_policy,
)


def test_default_policy_is_exponential():
    p = BackoffPolicy()
    assert p.strategy == "exponential"


def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="Invalid strategy"):
        BackoffPolicy(strategy="random")  # type: ignore[arg-type]


def test_invalid_base_raises():
    with pytest.raises(ValueError, match="base"):
        BackoffPolicy(base=-1.0)


def test_invalid_factor_raises():
    with pytest.raises(ValueError, match="factor"):
        BackoffPolicy(factor=0.0)


def test_invalid_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffPolicy(max_delay=-5.0)


def test_constant_strategy_returns_base():
    p = BackoffPolicy(strategy="constant", base=3.0)
    assert p.compute(0) == 3.0
    assert p.compute(5) == 3.0


def test_linear_strategy_grows():
    p = BackoffPolicy(strategy="linear", base=1.0, factor=2.0)
    assert p.compute(0) == 1.0
    assert p.compute(1) == 3.0
    assert p.compute(2) == 5.0


def test_exponential_strategy_doubles():
    p = BackoffPolicy(strategy="exponential", base=1.0, factor=2.0)
    assert p.compute(0) == 1.0
    assert p.compute(1) == 2.0
    assert p.compute(3) == 8.0


def test_fibonacci_strategy_grows_correctly():
    p = BackoffPolicy(strategy="fibonacci", base=1.0)
    assert p.compute(0) == 1.0
    assert p.compute(1) == 1.0
    assert p.compute(2) == 2.0
    assert p.compute(4) == 5.0


def test_max_delay_caps_result():
    p = BackoffPolicy(strategy="exponential", base=1.0, factor=2.0, max_delay=5.0)
    assert p.compute(10) == 5.0


def test_negative_attempt_raises():
    p = BackoffPolicy()
    with pytest.raises(ValueError, match="attempt"):
        p.compute(-1)


def test_make_backoff_policy_returns_instance():
    p = make_backoff_policy(strategy="linear", base=2.0, factor=1.5, max_delay=30.0)
    assert isinstance(p, BackoffPolicy)
    assert p.strategy == "linear"


def test_describe_backoff_policy_contains_fields():
    p = BackoffPolicy(strategy="constant", base=2.0, factor=1.0, max_delay=10.0)
    desc = describe_backoff_policy(p)
    assert "constant" in desc
    assert "2.0" in desc
