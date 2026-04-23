"""Tests for batchmark.backoff_config."""

import json
import pytest
from pathlib import Path

from batchmark.backoff import BackoffPolicy
from batchmark.backoff_config import (
    BackoffConfig,
    describe_backoff_config,
    load_backoff_config,
)


def write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data))
    return p


def test_default_config_is_valid():
    cfg = BackoffConfig()
    cfg.validate()  # should not raise


def test_invalid_strategy_raises():
    cfg = BackoffConfig(strategy="zigzag")
    with pytest.raises(ValueError, match="Invalid strategy"):
        cfg.validate()


def test_invalid_factor_raises():
    cfg = BackoffConfig(factor=-1.0)
    with pytest.raises(ValueError, match="factor"):
        cfg.validate()


def test_to_policy_returns_backoff_policy():
    cfg = BackoffConfig(strategy="linear", base=0.5, factor=1.0, max_delay=20.0)
    policy = cfg.to_policy()
    assert isinstance(policy, BackoffPolicy)
    assert policy.strategy == "linear"


def test_load_config_minimal(tmp_path):
    path = write_config(tmp_path, {})
    cfg = load_backoff_config(path)
    assert cfg.strategy == "exponential"
    assert cfg.base == 1.0


def test_load_config_full(tmp_path):
    path = write_config(tmp_path, {
        "backoff": {
            "strategy": "fibonacci",
            "base": 2.0,
            "factor": 3.0,
            "max_delay": 45.0,
        }
    })
    cfg = load_backoff_config(path)
    assert cfg.strategy == "fibonacci"
    assert cfg.base == 2.0
    assert cfg.factor == 3.0
    assert cfg.max_delay == 45.0


def test_load_config_invalid_strategy_raises(tmp_path):
    path = write_config(tmp_path, {"backoff": {"strategy": "bad"}})
    with pytest.raises(ValueError, match="Invalid strategy"):
        load_backoff_config(path)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_backoff_config("/nonexistent/path/config.json")


def test_describe_backoff_config_contains_strategy():
    cfg = BackoffConfig(strategy="constant", base=1.0, factor=1.0, max_delay=10.0)
    desc = describe_backoff_config(cfg)
    assert "constant" in desc
    assert "10.0" in desc
