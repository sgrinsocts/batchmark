"""Tests for ThrottleConfig."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from batchmark.throttle_config import (
    ThrottleConfig,
    describe_throttle_config,
    load_throttle_config,
)


def write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "throttle.json"
    p.write_text(json.dumps(data))
    return p


def test_default_config_is_valid():
    cfg = ThrottleConfig()
    cfg.validate()  # should not raise
    assert not cfg.is_active()


def test_enabled_with_positive_rate_is_active():
    cfg = ThrottleConfig(enabled=True, rate=10.0)
    cfg.validate()
    assert cfg.is_active()


def test_enabled_with_zero_rate_is_not_active():
    cfg = ThrottleConfig(enabled=True, rate=0.0)
    assert not cfg.is_active()


def test_invalid_negative_rate_raises():
    cfg = ThrottleConfig(enabled=True, rate=-1.0)
    with pytest.raises(ValueError, match="rate"):
        cfg.validate()


def test_invalid_burst_raises():
    cfg = ThrottleConfig(enabled=True, rate=5.0, burst=0)
    with pytest.raises(ValueError, match="burst"):
        cfg.validate()


def test_to_limiter_disabled_returns_unlimited():
    from batchmark.throttle import RateLimiter
    cfg = ThrottleConfig(enabled=False, rate=5.0)
    limiter = cfg.to_limiter()
    assert isinstance(limiter, RateLimiter)
    assert limiter.interval == 0.0


def test_to_limiter_enabled_returns_rate_limiter():
    from batchmark.throttle import RateLimiter
    cfg = ThrottleConfig(enabled=True, rate=4.0)
    limiter = cfg.to_limiter()
    assert isinstance(limiter, RateLimiter)
    assert pytest.approx(limiter.interval, rel=1e-3) == 0.25


def test_load_config_from_file(tmp_path):
    p = write_config(tmp_path, {"enabled": True, "rate": 2.0, "burst": 3})
    cfg = load_throttle_config(p)
    assert cfg.enabled is True
    assert cfg.rate == 2.0
    assert cfg.burst == 3


def test_load_config_minimal(tmp_path):
    p = write_config(tmp_path, {})
    cfg = load_throttle_config(p)
    assert not cfg.is_active()


def test_describe_disabled():
    cfg = ThrottleConfig()
    assert "disabled" in describe_throttle_config(cfg)


def test_describe_enabled():
    cfg = ThrottleConfig(enabled=True, rate=5.0, burst=2)
    desc = describe_throttle_config(cfg)
    assert "5.00" in desc
    assert "burst=2" in desc
