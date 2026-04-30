"""Tests for batchmark.window, batchmark.window_config, batchmark.window_runner."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from batchmark.config import BenchmarkConfig
from batchmark.window import WindowPolicy, describe_window_policy, make_window_policy
from batchmark.window_config import WindowConfig, describe_window_config, load_window_config
from batchmark.window_runner import run_with_window


# ---------------------------------------------------------------------------
# WindowPolicy unit tests
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    p = WindowPolicy()
    assert not p.enabled


def test_policy_enabled_when_max_calls_positive():
    p = WindowPolicy(max_calls=5, window_seconds=2.0)
    assert p.enabled


def test_policy_invalid_negative_max_calls():
    with pytest.raises(ValueError, match="max_calls"):
        WindowPolicy(max_calls=-1)


def test_policy_invalid_zero_window():
    with pytest.raises(ValueError, match="window_seconds"):
        WindowPolicy(max_calls=1, window_seconds=0)


def test_make_window_policy_returns_instance():
    p = make_window_policy(max_calls=10, window_seconds=5.0)
    assert isinstance(p, WindowPolicy)
    assert p.max_calls == 10


def test_describe_unlimited():
    assert "unlimited" in describe_window_policy(WindowPolicy())


def test_describe_limited():
    desc = describe_window_policy(WindowPolicy(max_calls=3, window_seconds=1.0))
    assert "3" in desc and "1.00" in desc


def test_acquire_unlimited_does_not_block():
    p = WindowPolicy()
    start = time.monotonic()
    for _ in range(20):
        p.acquire()
    assert time.monotonic() - start < 0.5


def test_current_count_tracks_calls():
    p = WindowPolicy(max_calls=10, window_seconds=5.0)
    p.acquire()
    p.acquire()
    assert p.current_count() == 2


# ---------------------------------------------------------------------------
# WindowConfig tests
# ---------------------------------------------------------------------------

def test_window_config_defaults():
    cfg = WindowConfig()
    assert cfg.max_calls == 0
    assert not cfg.is_active()


def test_window_config_to_policy():
    cfg = WindowConfig(max_calls=5, window_seconds=2.0)
    p = cfg.to_policy()
    assert isinstance(p, WindowPolicy)
    assert p.max_calls == 5


def test_load_window_config(tmp_path: Path):
    data = {"max_calls": 8, "window_seconds": 3.0}
    f = tmp_path / "window.json"
    f.write_text(json.dumps(data))
    cfg = load_window_config(f)
    assert cfg.max_calls == 8
    assert cfg.window_seconds == 3.0


def test_describe_window_config_unlimited():
    assert "unlimited" in describe_window_config(WindowConfig())


def test_describe_window_config_active():
    desc = describe_window_config(WindowConfig(max_calls=4, window_seconds=1.0))
    assert "4" in desc


# ---------------------------------------------------------------------------
# window_runner integration tests
# ---------------------------------------------------------------------------

def make_config(concurrency: int = 4) -> BenchmarkConfig:
    return BenchmarkConfig(concurrency=concurrency, jobs=[])


def noop_job():
    pass


def failing_job():
    raise RuntimeError("boom")


def test_run_with_no_policy_all_succeed():
    jobs = [noop_job] * 5
    results = run_with_window(jobs, make_config())
    assert all(r.success for r in results)
    assert len(results) == 5


def test_run_with_limited_policy_all_complete():
    policy = make_window_policy(max_calls=3, window_seconds=0.5)
    jobs = [noop_job] * 6
    results = run_with_window(jobs, make_config(concurrency=6), policy=policy)
    assert len(results) == 6


def test_run_with_failures_recorded():
    jobs = [noop_job, failing_job, noop_job]
    results = run_with_window(jobs, make_config())
    assert sum(1 for r in results if not r.success) == 1


def test_results_sorted_by_index():
    jobs = [noop_job] * 8
    results = run_with_window(jobs, make_config())
    assert [r.index for r in results] == list(range(8))
