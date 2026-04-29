"""Tests for batchmark.spillover, batchmark.spillover_config, and batchmark.spillover_runner."""

from __future__ import annotations

import pytest

from batchmark.config import BenchmarkConfig
from batchmark.spillover import (
    SpilloverPolicy,
    describe_spillover_policy,
    make_spillover_policy,
)
from batchmark.spillover_config import SpilloverConfig, describe_spillover_config, load_spillover_config
from batchmark.spillover_runner import run_with_spillover


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(**kwargs) -> BenchmarkConfig:
    defaults = dict(concurrency=1, iterations=1, output_format="text")
    defaults.update(kwargs)
    return BenchmarkConfig(**defaults)


def noop_job():
    return "primary"


def secondary_job():
    return "secondary"


# ---------------------------------------------------------------------------
# SpilloverPolicy unit tests
# ---------------------------------------------------------------------------

def test_default_policy_disabled():
    p = SpilloverPolicy()
    assert not p.enabled
    assert not p.should_spill()


def test_policy_enabled_when_flag_set():
    p = SpilloverPolicy(enabled=True, threshold=2)
    assert p.enabled


def test_policy_invalid_negative_threshold():
    with pytest.raises(ValueError, match="threshold"):
        SpilloverPolicy(enabled=True, threshold=-1)


def test_policy_invalid_negative_max_spilled():
    with pytest.raises(ValueError, match="max_spilled"):
        SpilloverPolicy(enabled=True, max_spilled=-5)


def test_should_spill_after_threshold():
    p = make_spillover_policy(threshold=2, enabled=True)
    p.record_primary()
    assert not p.should_spill()  # only 1 primary recorded
    p.record_primary()
    assert p.should_spill()      # threshold reached


def test_spill_count_increments():
    p = make_spillover_policy(threshold=0, enabled=True)
    assert p.spilled_count == 0
    p.record_spill()
    assert p.spilled_count == 1


def test_max_spilled_caps_spillover():
    p = make_spillover_policy(threshold=0, max_spilled=2, enabled=True)
    p.record_spill()
    p.record_spill()
    assert not p.should_spill()  # cap reached


def test_reset_clears_counters():
    p = make_spillover_policy(threshold=0, enabled=True)
    p.record_primary()
    p.record_spill()
    p.reset()
    assert p.spilled_count == 0


def test_describe_disabled():
    p = SpilloverPolicy()
    assert "disabled" in describe_spillover_policy(p)


def test_describe_enabled():
    p = make_spillover_policy(threshold=5, max_spilled=10, enabled=True)
    desc = describe_spillover_policy(p)
    assert "threshold=5" in desc
    assert "max_spilled=10" in desc


# ---------------------------------------------------------------------------
# SpilloverConfig tests
# ---------------------------------------------------------------------------

def test_load_spillover_config_defaults():
    cfg = load_spillover_config({})
    assert not cfg.enabled
    assert cfg.threshold == 0


def test_load_spillover_config_full():
    cfg = load_spillover_config({"spillover": {"enabled": True, "threshold": 3, "max_spilled": 5}})
    assert cfg.enabled
    assert cfg.threshold == 3
    assert cfg.max_spilled == 5


def test_spillover_config_invalid_threshold():
    with pytest.raises(ValueError):
        load_spillover_config({"spillover": {"enabled": True, "threshold": -1}})


def test_to_policy_returns_instance():
    cfg = SpilloverConfig(enabled=True, threshold=2, max_spilled=4)
    policy = cfg.to_policy()
    assert isinstance(policy, SpilloverPolicy)
    assert policy.enabled


def test_describe_config_disabled():
    cfg = SpilloverConfig()
    assert "disabled" in describe_spillover_config(cfg)


def test_describe_config_enabled():
    cfg = SpilloverConfig(enabled=True, threshold=3, max_spilled=6)
    desc = describe_spillover_config(cfg)
    assert "threshold=3" in desc


# ---------------------------------------------------------------------------
# spillover_runner integration tests
# ---------------------------------------------------------------------------

def test_run_no_policy_all_succeed():
    cfg = make_config()
    summary = run_with_spillover([noop_job, noop_job], cfg)
    assert len(summary.results) == 2
    assert all(r.success for r in summary.results)


def test_run_with_disabled_policy_ignores_secondary():
    cfg = make_config()
    policy = SpilloverPolicy(enabled=False)
    summary = run_with_spillover([noop_job, noop_job], cfg, policy=policy, secondary=secondary_job)
    assert all(r.success for r in summary.results)


def test_run_spills_after_threshold():
    cfg = make_config()
    policy = make_spillover_policy(threshold=1, enabled=True)
    spilled_results = []

    def tracking_secondary():
        spilled_results.append(True)
        return "spilled"

    jobs = [noop_job] * 4
    summary = run_with_spillover(jobs, cfg, policy=policy, secondary=tracking_secondary)
    assert len(summary.results) == 4
    # first job goes to primary, rest spill
    assert len(spilled_results) >= 1
