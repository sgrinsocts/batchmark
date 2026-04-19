"""Tests for batchmark.throttle."""

import time
import threading
import pytest

from batchmark.throttle import RateLimiter, make_rate_limiter


def test_unlimited_does_not_block():
    rl = RateLimiter(rate=0)
    start = time.monotonic()
    for _ in range(100):
        rl.acquire()
    assert time.monotonic() - start < 0.1


def test_make_rate_limiter_returns_instance():
    rl = make_rate_limiter(10.0)
    assert isinstance(rl, RateLimiter)
    assert rl.rate == 10.0


def test_make_rate_limiter_negative_raises():
    with pytest.raises(ValueError, match="rate must be >= 0"):
        make_rate_limiter(-1.0)


def test_callable_interface():
    rl = make_rate_limiter(0)
    rl()  # should not raise


def test_rate_limiter_slows_calls():
    """At 20 calls/sec, 5 calls should take >= ~0.15 s (first token free)."""
    rl = make_rate_limiter(20.0)
    start = time.monotonic()
    for _ in range(5):
        rl.acquire()
    elapsed = time.monotonic() - start
    # 4 waits of ~0.05 s each
    assert elapsed >= 0.15


def test_thread_safety():
    """Multiple threads acquiring from the same limiter should not raise."""
    rl = make_rate_limiter(0)  # unlimited to keep test fast
    errors = []

    def worker():
        try:
            for _ in range(50):
                rl.acquire()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []


def test_tokens_replenish_over_time():
    """After a pause tokens should replenish so next acquire is instant."""
    rl = make_rate_limiter(5.0)
    rl.acquire()  # consume initial token
    time.sleep(0.25)  # replenish ~1.25 tokens
    start = time.monotonic()
    rl.acquire()
    assert time.monotonic() - start < 0.05
