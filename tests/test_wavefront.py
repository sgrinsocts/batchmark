"""Tests for batchmark.wavefront."""

from __future__ import annotations

import threading
import time

import pytest

from batchmark.wavefront import (
    WavefrontPolicy,
    describe_wavefront_policy,
    make_wavefront_policy,
)


def test_default_policy_disabled():
    p = WavefrontPolicy()
    assert not p.enabled


def test_policy_enabled_when_max_in_flight_positive():
    p = WavefrontPolicy(max_in_flight=3)
    assert p.enabled


def test_policy_invalid_negative_max_in_flight():
    with pytest.raises(ValueError, match="max_in_flight"):
        WavefrontPolicy(max_in_flight=-1)


def test_policy_invalid_negative_timeout():
    with pytest.raises(ValueError, match="acquire_timeout"):
        WavefrontPolicy(acquire_timeout=-0.1)


def test_make_wavefront_policy_returns_instance():
    p = make_wavefront_policy(max_in_flight=2, acquire_timeout=1.0)
    assert isinstance(p, WavefrontPolicy)
    assert p.max_in_flight == 2


def test_acquire_and_release_tracks_active():
    p = WavefrontPolicy(max_in_flight=5, acquire_timeout=1.0)
    assert p.active == 0
    p.acquire()
    assert p.active == 1
    p.release()
    assert p.active == 0


def test_acquire_timeout_returns_false_when_exhausted():
    p = WavefrontPolicy(max_in_flight=1, acquire_timeout=0.05)
    assert p.acquire() is True
    # Semaphore is now exhausted; second acquire should time out
    assert p.acquire() is False
    p.release()


def test_unlimited_policy_never_blocks():
    p = WavefrontPolicy(max_in_flight=0, acquire_timeout=0.0)
    # Should always succeed regardless of how many times we call acquire
    for _ in range(20):
        result = p.acquire()
        assert result is True


def test_describe_unlimited():
    p = WavefrontPolicy()
    assert "unlimited" in describe_wavefront_policy(p)


def test_describe_limited():
    p = WavefrontPolicy(max_in_flight=4, acquire_timeout=2.0)
    desc = describe_wavefront_policy(p)
    assert "4" in desc
    assert "2.0" in desc


def test_concurrent_slots_respected():
    max_in_flight = 2
    p = WavefrontPolicy(max_in_flight=max_in_flight, acquire_timeout=1.0)
    peak = [0]
    lock = threading.Lock()

    def worker():
        p.acquire()
        with lock:
            peak[0] = max(peak[0], p.active)
        time.sleep(0.02)
        p.release()

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert peak[0] <= max_in_flight
