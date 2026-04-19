"""Tests for runner and reporter modules."""

import pytest
from batchmark.config import BenchmarkConfig
from batchmark.runner import run_benchmark, RunSummary
from batchmark.reporter import format_text, format_json, write_report


def make_config(num_jobs=4, concurrency=2):
    return BenchmarkConfig(num_jobs=num_jobs, concurrency=concurrency)


def noop_job(arg=None):
    return "ok"


def failing_job(arg=None):
    raise ValueError("intentional failure")


def test_run_all_succeed():
    config = make_config(num_jobs=5, concurrency=2)
    summary = run_benchmark(noop_job, config)
    assert summary.total == 5
    assert summary.succeeded == 5
    assert summary.failed == 0
    assert summary.success_rate == 1.0


def test_run_all_fail():
    config = make_config(num_jobs=3, concurrency=1)
    summary = run_benchmark(failing_job, config)
    assert summary.failed == 3
    assert summary.succeeded == 0
    assert summary.success_rate == 0.0
    for r in summary.results:
        assert "intentional failure" in r.error


def test_run_with_job_args():
    config = make_config(num_jobs=3, concurrency=3)
    jobs = [1, 2, 3]
    summary = run_benchmark(lambda x: x * 2, config, jobs=jobs)
    assert summary.total == 3
    outputs = {r.job_id: r.output for r in summary.results}
    assert outputs[0] == 2
    assert outputs[1] == 4
    assert outputs[2] == 6


def test_results_sorted_by_job_id():
    config = make_config(num_jobs=8, concurrency=4)
    summary = run_benchmark(noop_job, config)
    ids = [r.job_id for r in summary.results]
    assert ids == sorted(ids)


def test_format_text():
    config = make_config(num_jobs=2)
    summary = run_benchmark(noop_job, config)
    report = format_text(summary)
    assert "Benchmark Report" in report
    assert "Succeeded" in report


def test_format_json():
    import json
    config = make_config(num_jobs=2)
    summary = run_benchmark(noop_job, config)
    data = json.loads(format_json(summary))
    assert data["total"] == 2
    assert "results" in data


def test_write_report_returns_string():
    import io
    config = make_config(num_jobs=2)
    summary = run_benchmark(noop_job, config)
    buf = io.StringIO()
    result = write_report(summary, fmt="text", stream=buf)
    assert isinstance(result, str)
    assert buf.getvalue().strip() == result.strip()
