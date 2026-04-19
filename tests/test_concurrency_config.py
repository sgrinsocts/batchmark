"""Tests for ConcurrencyConfig loading and validation."""

from __future__ import annotations

import json
import os
import pytest

from batchmark.concurrency_config import (
    ConcurrencyConfig,
    load_concurrency_config,
    describe_concurrency_config,
)


def write_config(tmp_path, data: dict) -> str:
    p = tmp_path / "concurrency.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_default_config_valid():
    cfg = ConcurrencyConfig()
    cfg.validate()
    assert cfg.max_workers == 4
    assert cfg.queue_timeout is None


def test_invalid_max_workers():
    cfg = ConcurrencyConfig(max_workers=0)
    with pytest.raises(ValueError, match="max_workers"):
        cfg.validate()


def test_invalid_queue_timeout():
    cfg = ConcurrencyConfig(queue_timeout=-1.0)
    with pytest.raises(ValueError, match="queue_timeout"):
        cfg.validate()


def test_load_config_minimal(tmp_path):
    path = write_config(tmp_path, {"max_workers": 8})
    cfg = load_concurrency_config(path)
    assert cfg.max_workers == 8
    assert cfg.queue_timeout is None


def test_load_config_full(tmp_path):
    path = write_config(tmp_path, {"max_workers": 2, "queue_timeout": 5.0})
    cfg = load_concurrency_config(path)
    assert cfg.max_workers == 2
    assert cfg.queue_timeout == 5.0


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_concurrency_config("/nonexistent/path.json")


def test_describe_unlimited(tmp_path):
    cfg = ConcurrencyConfig(max_workers=4)
    desc = describe_concurrency_config(cfg)
    assert "4" in desc
    assert "unlimited" in desc


def test_describe_with_timeout():
    cfg = ConcurrencyConfig(max_workers=2, queue_timeout=3.5)
    desc = describe_concurrency_config(cfg)
    assert "3.5" in desc
