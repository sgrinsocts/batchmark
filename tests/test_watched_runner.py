"""Tests for batchmark.watched_runner."""
import pytest
from batchmark.config import BenchmarkConfig
from batchmark.watcher_config import WatcherConfig
from batchmark.watched_runner import run_on_change


def make_config(n: int = 3) -> BenchmarkConfig:
    return BenchmarkConfig(job_count=n, concurrency=1)


def noop_job(idx: int) -> None:
    pass


def test_run_on_change_disabled_runs_once():
    cfg = make_config(3)
    wcfg = WatcherConfig(paths=[], enabled=False)
    runs = run_on_change(noop_job, cfg, wcfg)
    assert len(runs) == 1
    assert len(runs[0]) == 3


def test_run_on_change_no_paths_runs_once():
    cfg = make_config(2)
    wcfg = WatcherConfig(paths=[], enabled=True)
    runs = run_on_change(noop_job, cfg, wcfg)
    assert len(runs) == 1


def test_run_on_change_results_have_correct_count():
    cfg = make_config(4)
    wcfg = WatcherConfig(paths=[], enabled=False)
    runs = run_on_change(noop_job, cfg, wcfg)
    assert all(len(r) == 4 for r in runs)
