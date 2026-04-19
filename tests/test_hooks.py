"""Tests for lifecycle hooks and progress tracker."""
import pytest
from batchmark.hooks import HookRegistry, get_registry, reset_registry
from batchmark.progress import ProgressTracker
from batchmark.runner import JobResult


@pytest.fixture(autouse=True)
def clean_registry():
    reset_registry()
    yield
    reset_registry()


def test_fire_start_calls_all():
    reg = HookRegistry()
    calls = []
    reg.register_start(lambda cfg: calls.append(("start", cfg)))
    reg.register_start(lambda cfg: calls.append(("start2", cfg)))
    reg.fire_start("cfg")
    assert len(calls) == 2


def test_fire_job_complete():
    reg = HookRegistry()
    seen = []
    reg.register_job_complete(lambda r: seen.append(r))
    result = JobResult(job_id=0, success=True, duration=0.1, error=None)
    reg.fire_job_complete(result)
    assert seen[0] is result


def test_fire_finish():
    reg = HookRegistry()
    finished = []
    reg.register_finish(lambda s: finished.append(s))
    reg.fire_finish("summary")
    assert finished == ["summary"]


def test_get_registry_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_reset_registry():
    r1 = get_registry()
    reset_registry()
    r2 = get_registry()
    assert r1 is not r2


def test_progress_tracker_counts():
    pt = ProgressTracker(total=4, silent=True)
    pt.record(success=True)
    pt.record(success=True)
    pt.record(success=False)
    assert pt.completed == 3
    assert pt.failed == 1
    assert pt.success_count == 2


def test_progress_tracker_zero_total():
    pt = ProgressTracker(total=0, silent=True)
    assert pt.success_count == 0
