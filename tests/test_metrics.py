"""Tests for batchmark.metrics module."""

import pytest
from batchmark.metrics import (
    MetricsSummary,
    PercentileStats,
    collect_error_types,
    compute_metrics,
    compute_percentiles,
)
from batchmark.runner import JobResult


def make_result(duration: float, success: bool = True, error=None) -> JobResult:
    return JobResult(job_id="j", duration=duration, success=success, error=error)


def test_compute_percentiles_empty():
    p = compute_percentiles([])
    assert p.p50 == 0.0 and p.p99 == 0.0


def test_compute_percentiles_single():
    p = compute_percentiles([1.0])
    assert p.p50 == 1.0
    assert p.p99 == 1.0


def test_compute_percentiles_values():
    durations = list(range(1, 101))  # 1..100
    p = compute_percentiles(durations)
    assert p.p50 == 50
    assert p.p90 == 90
    assert p.p95 == 95
    assert p.p99 == 99


def test_collect_error_types_no_errors():
    results = [make_result(0.1), make_result(0.2)]
    assert collect_error_types(results) == {}


def test_collect_error_types_mixed():
    results = [
        make_result(0.1, success=False, error=ValueError("v")),
        make_result(0.2, success=False, error=ValueError("v2")),
        make_result(0.3, success=False, error=RuntimeError("r")),
        make_result(0.4),
    ]
    counts = collect_error_types(results)
    assert counts["ValueError"] == 2
    assert counts["RuntimeError"] == 1


def test_compute_metrics_empty_raises():
    with pytest.raises(ValueError):
        compute_metrics([])


def test_compute_metrics_all_success():
    results = [make_result(d) for d in [0.1, 0.2, 0.3, 0.4, 0.5]]
    m = compute_metrics(results)
    assert m.total == 5
    assert m.succeeded == 5
    assert m.failed == 0
    assert m.success_rate == 1.0
    assert abs(m.min_duration - 0.1) < 1e-9
    assert abs(m.max_duration - 0.5) < 1e-9


def test_compute_metrics_partial_failure():
    results = [
        make_result(0.1),
        make_result(0.2, success=False, error=RuntimeError("boom")),
    ]
    m = compute_metrics(results)
    assert m.succeeded == 1
    assert m.failed == 1
    assert m.success_rate == 0.5
    assert m.error_types == {"RuntimeError": 1}


def test_compute_metrics_stddev_single():
    results = [make_result(1.0)]
    m = compute_metrics(results)
    assert m.stddev_duration == 0.0
