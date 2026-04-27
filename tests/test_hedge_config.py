"""Tests for batchmark.hedge_config module."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from batchmark.hedge import HedgePolicy
from batchmark.hedge_config import (
    HedgeConfig,
    load_hedge_config,
    describe_hedge_config,
)


def write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "hedge.json"
    p.write_text(json.dumps(data))
    return p


def test_default_config_is_valid():
    cfg = HedgeConfig()
    cfg.validate()
    assert cfg.enabled is False


def test_invalid_delay_raises():
    cfg = HedgeConfig(delay_seconds=-0.5)
    with pytest.raises(ValueError, match="delay_seconds"):
        cfg.validate()


def test_invalid_max_hedges_raises():
    cfg = HedgeConfig(max_hedges=0)
    with pytest.raises(ValueError, match="max_hedges"):
        cfg.validate()


def test_to_policy_returns_hedge_policy():
    cfg = HedgeConfig(enabled=True, delay_seconds=0.3, max_hedges=2)
    policy = cfg.to_policy()
    assert isinstance(policy, HedgePolicy)
    assert policy.enabled is True
    assert policy.delay_seconds == 0.3
    assert policy.max_hedges == 2


def test_load_config_minimal(tmp_path):
    p = write_config(tmp_path, {})
    cfg = load_hedge_config(p)
    assert cfg.enabled is False


def test_load_config_full(tmp_path):
    p = write_config(tmp_path, {"hedge": {"enabled": True, "delay_seconds": 0.1, "max_hedges": 3}})
    cfg = load_hedge_config(p)
    assert cfg.enabled is True
    assert cfg.delay_seconds == 0.1
    assert cfg.max_hedges == 3


def test_load_config_invalid_raises(tmp_path):
    p = write_config(tmp_path, {"hedge": {"delay_seconds": -1}})
    with pytest.raises(ValueError):
        load_hedge_config(p)


def test_describe_disabled():
    cfg = HedgeConfig(enabled=False)
    assert "disabled" in describe_hedge_config(cfg)


def test_describe_enabled():
    cfg = HedgeConfig(enabled=True, delay_seconds=0.5, max_hedges=1)
    desc = describe_hedge_config(cfg)
    assert "enabled" in desc
    assert "0.5" in desc


def test_is_limited_reflects_enabled():
    assert HedgeConfig(enabled=True).is_limited() is True
    assert HedgeConfig(enabled=False).is_limited() is False
