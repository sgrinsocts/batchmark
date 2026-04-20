"""Tests for batchmark.circuit_breaker."""

import time
import pytest
from unittest.mock import patch

from batchmark.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    make_circuit_breaker,
)


def test_initial_state_is_closed():
    cb = CircuitBreaker()
    assert cb.state is CircuitState.CLOSED


def test_allow_request_when_closed():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.allow_request() is True


def test_trips_after_threshold_failures():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure()
    assert cb.state is CircuitState.OPEN


def test_open_circuit_blocks_requests():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.allow_request() is False


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    cb.record_failure()
    # Only 1 failure after reset — should still be closed
    assert cb.state is CircuitState.CLOSED


def test_transitions_to_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    cb.record_failure()
    assert cb.state is CircuitState.OPEN
    time.sleep(0.06)
    assert cb.state is CircuitState.HALF_OPEN


def test_half_open_allows_limited_calls():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05, half_open_max_calls=1)
    cb.record_failure()
    time.sleep(0.06)
    assert cb.allow_request() is True
    cb._half_open_calls = 1
    assert cb.allow_request() is False


def test_half_open_success_closes_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    cb.record_failure()
    time.sleep(0.06)
    _ = cb.state  # trigger half-open transition
    cb.record_success()
    assert cb.state is CircuitState.CLOSED


def test_half_open_failure_reopens_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    cb.record_failure()
    time.sleep(0.06)
    _ = cb.state  # trigger half-open
    cb.record_failure()
    assert cb.state is CircuitState.OPEN


def test_reset_clears_all_state():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state is CircuitState.OPEN
    cb.reset()
    assert cb.state is CircuitState.CLOSED
    assert cb.allow_request() is True


def test_invalid_failure_threshold_raises():
    with pytest.raises(ValueError, match="failure_threshold"):
        CircuitBreaker(failure_threshold=0)


def test_invalid_recovery_timeout_raises():
    with pytest.raises(ValueError, match="recovery_timeout"):
        CircuitBreaker(recovery_timeout=0.0)


def test_invalid_half_open_max_calls_raises():
    with pytest.raises(ValueError, match="half_open_max_calls"):
        CircuitBreaker(half_open_max_calls=0)


def test_make_circuit_breaker_returns_instance():
    cb = make_circuit_breaker(failure_threshold=10, recovery_timeout=60.0)
    assert isinstance(cb, CircuitBreaker)
    assert cb.failure_threshold == 10
    assert cb.recovery_timeout == 60.0
