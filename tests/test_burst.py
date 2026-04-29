"""Tests for batchmark.burst and batchmark.burst_config."""

from __future__ import annotations

import time
import pytest

from batchmark.burst import BurstPolicy, make_burst_policy, describe_burst_policy


# ---------------------------------------------------------------------------
# BurstPolicy construction
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    p = BurstPolicy()
    assert not p.enabled


def test_policy_enabled_when_strategy_and_rate_set():
    p = make_burst_policy(strategy="token_bucket", steady_rate=10.0, burst_size=5)
    assert p.enabled


def test_policy_disabled_when_rate_zero():
    p = make_burst_policy(strategy="token_bucket", steady_rate=0.0, burst_size=5)
    assert not p.enabled


def test_policy_invalid_strategy_raises():
    with pytest.raises(ValueError, match="strategy"):
        BurstPolicy(strategy="leaky_bucket")


def test_policy_invalid_negative_rate_raises():
    with pytest.raises(ValueError, match="steady_rate"):
        BurstPolicy(strategy="token_bucket", steady_rate=-1.0)


def test_policy_invalid_negative_burst_raises():
    with pytest.raises(ValueError, match="burst_size"):
        BurstPolicy(strategy="token_bucket", steady_rate=5.0, burst_size=-1)


def test_policy_invalid_window_zero_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        BurstPolicy(strategy="token_bucket", steady_rate=5.0, window_seconds=0)


# ---------------------------------------------------------------------------
# acquire() behaviour
# ---------------------------------------------------------------------------

def test_acquire_disabled_returns_zero():
    p = BurstPolicy()  # disabled
    wait = p.acquire()
    assert wait == 0.0


def test_acquire_consumes_burst_tokens_immediately():
    """With burst_size=5 and steady_rate=1, first 5 calls should be instant."""
    p = make_burst_policy(strategy="token_bucket", steady_rate=1.0, burst_size=5)
    for _ in range(5):
        wait = p.acquire()
        assert wait == 0.0, "burst tokens should allow instant acquisition"


def test_acquire_blocks_after_burst_exhausted():
    """After burst tokens are gone, the next call must wait."""
    p = make_burst_policy(strategy="token_bucket", steady_rate=10.0, burst_size=0)
    # force tokens to 0
    p._tokens = 0.0
    start = time.monotonic()
    wait = p.acquire()
    elapsed = time.monotonic() - start
    assert wait > 0
    assert elapsed >= wait * 0.9  # allow small timing slack


# ---------------------------------------------------------------------------
# describe_burst_policy
# ---------------------------------------------------------------------------

def test_describe_disabled():
    p = BurstPolicy()
    assert describe_burst_policy(p) == "burst: disabled"


def test_describe_enabled_contains_fields():
    p = make_burst_policy(strategy="token_bucket", steady_rate=5.0, burst_size=3)
    desc = describe_burst_policy(p)
    assert "token_bucket" in desc
    assert "5.0" in desc
    assert "3" in desc


# ---------------------------------------------------------------------------
# burst_config helpers
# ---------------------------------------------------------------------------

def test_to_policy_from_dict():
    from batchmark.burst_config import to_policy
    cfg = {"strategy": "token_bucket", "steady_rate": 20.0, "burst_size": 10}
    p = to_policy(cfg)
    assert isinstance(p, BurstPolicy)
    assert p.steady_rate == 20.0
    assert p.burst_size == 10


def test_to_policy_invalid_raises():
    from batchmark.burst_config import to_policy
    with pytest.raises(ValueError):
        to_policy({"strategy": "bad"})


def test_is_active_true():
    from batchmark.burst_config import is_active
    assert is_active({"strategy": "token_bucket", "steady_rate": 5.0})


def test_is_active_false_when_none_strategy():
    from batchmark.burst_config import is_active
    assert not is_active({"strategy": "none", "steady_rate": 5.0})


def test_load_burst_config(tmp_path):
    from batchmark.burst_config import load_burst_config
    cfg_file = tmp_path / "batchmark.toml"
    cfg_file.write_text(
        "[burst]\nstrategy = \"token_bucket\"\nsteady_rate = 8.0\nburst_size = 4\n"
    )
    p = load_burst_config(cfg_file)
    assert p.strategy == "token_bucket"
    assert p.steady_rate == 8.0
    assert p.burst_size == 4
