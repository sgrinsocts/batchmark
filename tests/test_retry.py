"""Tests for batchmark.retry."""
import pytest
from unittest.mock import MagicMock
from batchmark.retry import RetryPolicy, with_retry, make_retry_policy


def test_retry_policy_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 1
    assert p.backoff_base == 0.5


def test_retry_policy_invalid_attempts():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_retry_policy_invalid_backoff():
    with pytest.raises(ValueError):
        RetryPolicy(backoff_base=-1)


def test_delay_capped_at_max():
    p = RetryPolicy(backoff_base=1.0, backoff_max=3.0)
    assert p.delay(10) == 3.0


def test_delay_grows_exponentially():
    p = RetryPolicy(backoff_base=1.0, backoff_max=100.0)
    assert p.delay(0) == 1.0
    assert p.delay(1) == 2.0
    assert p.delay(2) == 4.0


def test_with_retry_succeeds_first_try():
    fn = MagicMock(return_value=42)
    result = with_retry(fn, RetryPolicy(max_attempts=3))
    assert result == 42
    fn.assert_called_once()


def test_with_retry_retries_on_failure(monkeypatch):
    monkeypatch.setattr("batchmark.retry.time.sleep", lambda _: None)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("fail")
        return "ok"

    result = with_retry(flaky, RetryPolicy(max_attempts=3, backoff_base=0.0))
    assert result == "ok"
    assert calls["n"] == 3


def test_with_retry_raises_after_exhaustion(monkeypatch):
    monkeypatch.setattr("batchmark.retry.time.sleep", lambda _: None)
    fn = MagicMock(side_effect=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        with_retry(fn, RetryPolicy(max_attempts=3, backoff_base=0.0))
    assert fn.call_count == 3


def test_make_retry_policy_from_dict():
    cfg = {"max_attempts": 5, "backoff_base": 1.0, "backoff_max": 8.0}
    p = make_retry_policy(cfg)
    assert p.max_attempts == 5
    assert p.backoff_base == 1.0
    assert p.backoff_max == 8.0


def test_make_retry_policy_defaults():
    p = make_retry_policy({})
    assert p.max_attempts == 1
