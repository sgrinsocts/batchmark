"""Tests for batchmark.jitter_config."""

from __future__ import annotations

import pytest
import yaml

from batchmark.jitter import JitterPolicy
from batchmark.jitter_config import (
    JitterConfig,
    describe_jitter_config,
    load_jitter_config,
)


def write_config(tmp_path, data: dict) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data))
    return str(path)


def test_default_config_valid():
    cfg = JitterConfig()
    cfg.validate()  # should not raise


def test_invalid_strategy_raises():
    cfg = JitterConfig(strategy="bogus")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid jitter strategy"):
        cfg.validate()


def test_invalid_max_seconds_raises():
    cfg = JitterConfig(max_seconds=-0.1)
    with pytest.raises(ValueError, match="max_seconds"):
        cfg.validate()


def test_to_policy_returns_jitter_policy():
    cfg = JitterConfig(strategy="full", max_seconds=0.5)
    policy = cfg.to_policy()
    assert isinstance(policy, JitterPolicy)
    assert policy.strategy == "full"


def test_load_config_minimal(tmp_path):
    path = write_config(tmp_path, {})
    cfg = load_jitter_config(path)
    assert cfg.strategy == "none"
    assert cfg.max_seconds == 1.0


def test_load_config_full(tmp_path):
    path = write_config(
        tmp_path,
        {"jitter": {"strategy": "decorrelated", "max_seconds": 2.5, "seed": 99}},
    )
    cfg = load_jitter_config(path)
    assert cfg.strategy == "decorrelated"
    assert cfg.max_seconds == 2.5
    assert cfg.seed == 99


def test_load_config_invalid_strategy_raises(tmp_path):
    path = write_config(tmp_path, {"jitter": {"strategy": "random"}})
    with pytest.raises(ValueError, match="Invalid jitter strategy"):
        load_jitter_config(path)


def test_describe_config():
    cfg = JitterConfig(strategy="equal", max_seconds=1.0)
    desc = describe_jitter_config(cfg)
    assert "equal" in desc
    assert "1.0" in desc
