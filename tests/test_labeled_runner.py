"""Tests for batchmark.labeled_runner."""
import pytest
from batchmark.labels import make_labeled_job
from batchmark.labeled_runner import run_labeled, run_by_label_group
from batchmark.config import BenchmarkConfig


def make_config(**kwargs) -> BenchmarkConfig:
    defaults = dict(jobs=1, concurrency=1, output="text")
    defaults.update(kwargs)
    return BenchmarkConfig(**defaults)


def noop():
    pass


def test_run_labeled_no_selector_runs_all():
    jobs = [make_labeled_job(noop, f"j{i}", env="prod") for i in range(3)]
    results = run_labeled(jobs, make_config(jobs=3))
    assert len(results) == 3
    assert all(r.success for r in results)


def test_run_labeled_with_selector_filters():
    jobs = [
        make_labeled_job(noop, "a", env="prod"),
        make_labeled_job(noop, "b", env="staging"),
        make_labeled_job(noop, "c", env="prod"),
    ]
    results = run_labeled(jobs, make_config(jobs=2), selector={"env": "prod"})
    assert len(results) == 2


def test_run_labeled_selector_no_match_returns_empty():
    jobs = [make_labeled_job(noop, "a", env="prod")]
    results = run_labeled(jobs, make_config(jobs=0), selector={"env": "staging"})
    assert results == []


def test_run_by_label_group_returns_dict():
    jobs = [
        make_labeled_job(noop, "a", tier="fast"),
        make_labeled_job(noop, "b", tier="slow"),
        make_labeled_job(noop, "c", tier="fast"),
    ]
    groups = run_by_label_group(jobs, make_config(jobs=2), key="tier")
    assert set(groups.keys()) == {"fast", "slow"}
    assert len(groups["fast"]) == 2
    assert len(groups["slow"]) == 1


def test_run_by_label_group_all_succeed():
    jobs = [make_labeled_job(noop, f"j{i}", tier="x") for i in range(4)]
    groups = run_by_label_group(jobs, make_config(jobs=4), key="tier")
    assert all(r.success for r in groups["x"])
