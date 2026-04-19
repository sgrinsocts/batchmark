"""Tests for batchmark.timeout and batchmark.timeout_config."""
import time
import pytest

from batchmark.timeout import TimeoutPolicy, make_timeout_policy, run_with_timeout
from batchmark.timeout_config import TimeoutConfig, load_timeout_config, describe_timeout_config


# --- TimeoutPolicy ---

def test_policy_defaults():
    p = TimeoutPolicy()
    assert p.seconds is None
    assert not p.enabled


def test_policy_enabled():
    p = TimeoutPolicy(seconds=2.0)
    assert p.enabled


def test_policy_invalid():
    with pytest.raises(ValueError):
        TimeoutPolicy(seconds=0)
    with pytest.raises(ValueError):
        TimeoutPolicy(seconds=-1)


def test_make_timeout_policy():
    p = make_timeout_policy(5.0)
    assert p.seconds == 5.0


# --- run_with_timeout ---

def test_no_timeout_runs_normally():
    policy = TimeoutPolicy()
    result = run_with_timeout(lambda: 42, policy)
    assert result == 42


def test_within_timeout_succeeds():
    policy = TimeoutPolicy(seconds=2.0)
    result = run_with_timeout(lambda: "ok", policy)
    assert result == "ok"


def test_exceeds_timeout_raises():
    policy = TimeoutPolicy(seconds=0.05)
    with pytest.raises(TimeoutError):
        run_with_timeout(lambda: time.sleep(5), policy)


# --- TimeoutConfig / load_timeout_config ---

def test_load_no_section():
    cfg = load_timeout_config({})
    assert cfg.seconds is None
    assert not cfg.is_limited()


def test_load_with_seconds():
    cfg = load_timeout_config({"timeout": {"seconds": "3.5"}})
    assert cfg.seconds == 3.5
    assert cfg.is_limited()


def test_to_policy():
    cfg = TimeoutConfig(seconds=1.0)
    p = cfg.to_policy()
    assert isinstance(p, TimeoutPolicy)
    assert p.seconds == 1.0


def test_describe_no_limit():
    assert describe_timeout_config(TimeoutConfig()) == "timeout: none"


def test_describe_with_limit():
    assert describe_timeout_config(TimeoutConfig(seconds=10.0)) == "timeout: 10.0s per job"
