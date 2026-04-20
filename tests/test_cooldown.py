"""Tests for batchmark.cooldown."""

import time
import pytest

from batchmark.cooldown import (
    CooldownPolicy,
    make_cooldown_policy,
    run_with_cooldown,
)


# ---------------------------------------------------------------------------
# CooldownPolicy unit tests
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    p = CooldownPolicy()
    assert not p.enabled


def test_policy_enabled_when_seconds_positive():
    p = CooldownPolicy(seconds=0.5)
    assert p.enabled


def test_policy_invalid_negative_seconds():
    with pytest.raises(ValueError, match="cooldown seconds must be >= 0"):
        CooldownPolicy(seconds=-1.0)


def test_make_cooldown_policy_returns_instance():
    p = make_cooldown_policy(0.1)
    assert isinstance(p, CooldownPolicy)
    assert p.seconds == 0.1


def test_make_cooldown_policy_negative_raises():
    with pytest.raises(ValueError):
        make_cooldown_policy(-0.5)


def test_ready_in_zero_when_disabled():
    p = CooldownPolicy(seconds=0.0)
    assert p.ready_in() == 0.0


def test_ready_in_positive_right_after_record():
    p = CooldownPolicy(seconds=5.0)
    p.record()
    assert p.ready_in() > 0.0


def test_ready_in_zero_after_cooldown_elapsed():
    p = CooldownPolicy(seconds=0.05)
    p.record()
    time.sleep(0.1)
    assert p.ready_in() == 0.0


def test_wait_does_not_block_when_disabled():
    p = CooldownPolicy(seconds=0.0)
    start = time.monotonic()
    p.wait()
    assert time.monotonic() - start < 0.05


def test_wait_blocks_for_cooldown():
    p = CooldownPolicy(seconds=0.1)
    p.record()
    start = time.monotonic()
    p.wait()
    assert time.monotonic() - start >= 0.05  # some gap enforced


# ---------------------------------------------------------------------------
# run_with_cooldown integration tests
# ---------------------------------------------------------------------------

def test_run_with_cooldown_no_policy_returns_all():
    calls = []
    jobs = [lambda i=i: calls.append(i) or i for i in range(3)]
    results = run_with_cooldown(jobs)
    assert results == [0, 1, 2]


def test_run_with_cooldown_collects_results():
    jobs = [lambda v=v: v * 2 for v in range(4)]
    policy = make_cooldown_policy(0.0)
    results = run_with_cooldown(jobs, policy)
    assert results == [0, 2, 4, 6]


def test_run_with_cooldown_empty_jobs():
    results = run_with_cooldown([], make_cooldown_policy(0.0))
    assert results == []


def test_run_with_cooldown_enforces_gap():
    policy = make_cooldown_policy(0.05)
    timestamps: list[float] = []

    def timed_job():
        timestamps.append(time.monotonic())

    run_with_cooldown([timed_job, timed_job, timed_job], policy)
    assert len(timestamps) == 3
    for i in range(1, len(timestamps)):
        assert timestamps[i] - timestamps[i - 1] >= 0.04
