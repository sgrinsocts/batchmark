"""Tests for batchmark.budget."""
import time
import pytest
from batchmark.budget import TimeBudget, make_budget, check_budget


def test_budget_not_exceeded_immediately():
    b = TimeBudget(max_seconds=10.0)
    assert not b.is_exceeded()


def test_budget_exceeded_after_sleep():
    b = TimeBudget(max_seconds=0.05)
    time.sleep(0.1)
    assert b.is_exceeded()


def test_remaining_decreases():
    b = TimeBudget(max_seconds=5.0)
    r1 = b.remaining()
    time.sleep(0.05)
    r2 = b.remaining()
    assert r2 < r1


def test_remaining_never_negative():
    b = TimeBudget(max_seconds=0.01)
    time.sleep(0.05)
    assert b.remaining() == 0.0


def test_reset_restores_budget():
    b = TimeBudget(max_seconds=0.05)
    time.sleep(0.1)
    assert b.is_exceeded()
    b.reset()
    assert not b.is_exceeded()


def test_make_budget_none_returns_none():
    assert make_budget(None) is None


def test_make_budget_positive():
    b = make_budget(3.0)
    assert b is not None
    assert b.max_seconds == 3.0


def test_make_budget_zero_raises():
    with pytest.raises(ValueError):
        make_budget(0)


def test_make_budget_negative_raises():
    with pytest.raises(ValueError):
        make_budget(-1.0)


def test_check_budget_no_budget_ok():
    check_budget(None)  # should not raise


def test_check_budget_exceeded_raises():
    b = TimeBudget(max_seconds=0.01)
    time.sleep(0.05)
    with pytest.raises(RuntimeError, match="Time budget exceeded"):
        check_budget(b, label="test")


def test_check_budget_not_exceeded_ok():
    b = TimeBudget(max_seconds=10.0)
    check_budget(b)  # should not raise
