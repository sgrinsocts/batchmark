"""Tests for batchmark.shedding and batchmark.shedding_runner."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from batchmark.config import BenchmarkConfig
from batchmark.shedding import (
    SheddingPolicy,
    describe_shedding_policy,
    make_shedding_policy,
)
from batchmark.shedding_config import (
    SheddingConfig,
    describe_shedding_config,
    load_shedding_config,
)
from batchmark.shedding_runner import run_with_shedding


# ---------------------------------------------------------------------------
# SheddingPolicy unit tests
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    p = SheddingPolicy()
    assert not p.enabled
    assert not p.should_shed(queue_depth=9999)


def test_policy_enabled_when_flag_set():
    p = make_shedding_policy(enabled=True, load_threshold=0.9)
    assert p.enabled


def test_policy_invalid_negative_queue_depth():
    with pytest.raises(ValueError, match="max_queue_depth"):
        SheddingPolicy(enabled=True, max_queue_depth=-1)


def test_policy_invalid_threshold_zero():
    with pytest.raises(ValueError, match="load_threshold"):
        SheddingPolicy(enabled=True, load_threshold=0.0)


def test_policy_invalid_threshold_above_one():
    with pytest.raises(ValueError, match="load_threshold"):
        SheddingPolicy(enabled=True, load_threshold=1.5)


def test_policy_invalid_sample_window():
    with pytest.raises(ValueError, match="sample_window"):
        SheddingPolicy(enabled=True, sample_window=0.0)


def test_shed_when_queue_depth_exceeded():
    p = make_shedding_policy(enabled=True, max_queue_depth=3)
    assert p.should_shed(queue_depth=3)
    assert not p.should_shed(queue_depth=2)


def test_describe_disabled():
    assert "disabled" in describe_shedding_policy(SheddingPolicy())


def test_describe_enabled():
    p = make_shedding_policy(enabled=True, load_threshold=0.8, max_queue_depth=5)
    desc = describe_shedding_policy(p)
    assert "80%" in desc
    assert "max_queue=5" in desc


# ---------------------------------------------------------------------------
# SheddingConfig tests
# ---------------------------------------------------------------------------

def test_config_to_policy_returns_policy():
    cfg = SheddingConfig(enabled=True, load_threshold=0.75)
    policy = cfg.to_policy()
    assert isinstance(policy, SheddingPolicy)
    assert policy.enabled


def test_load_shedding_config(tmp_path: Path):
    data = {"enabled": True, "load_threshold": 0.6, "max_queue_depth": 10, "sample_window": 3.0}
    p = tmp_path / "shedding.json"
    p.write_text(json.dumps(data))
    cfg = load_shedding_config(p)
    assert cfg.enabled
    assert cfg.load_threshold == 0.6
    assert cfg.max_queue_depth == 10


def test_describe_shedding_config_disabled():
    assert "disabled" in describe_shedding_config(SheddingConfig())


def test_describe_shedding_config_enabled():
    cfg = SheddingConfig(enabled=True, load_threshold=0.5, max_queue_depth=4)
    desc = describe_shedding_config(cfg)
    assert "50%" in desc


# ---------------------------------------------------------------------------
# shedding_runner integration tests
# ---------------------------------------------------------------------------

def make_config(concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(concurrency=concurrency, total_jobs=5)


def noop_job() -> None:
    pass


def test_run_no_policy_all_succeed():
    jobs = [noop_job] * 5
    summary = run_with_shedding(jobs, make_config(), policy=None)
    assert len(summary.results) == 5
    assert all(r.success for r in summary.results)


def test_run_shed_by_queue_depth():
    policy = make_shedding_policy(enabled=True, max_queue_depth=2)
    jobs = [noop_job] * 5
    summary = run_with_shedding(jobs, make_config(), policy=policy)
    shed = [r for r in summary.results if r.error == "shed"]
    assert len(shed) >= 3


def test_shed_jobs_recorded_as_failures():
    policy = make_shedding_policy(enabled=True, max_queue_depth=1)
    jobs = [noop_job] * 4
    summary = run_with_shedding(jobs, make_config(), policy=policy)
    failed = [r for r in summary.results if not r.success]
    assert all(r.error == "shed" for r in failed)


def test_shed_count_on_summary():
    policy = make_shedding_policy(enabled=True, max_queue_depth=2)
    jobs = [noop_job] * 5
    summary = run_with_shedding(jobs, make_config(), policy=policy)
    assert summary.shed_count == len([r for r in summary.results if r.error == "shed"])
