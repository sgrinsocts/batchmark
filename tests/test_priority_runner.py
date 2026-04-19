"""Tests for batchmark.priority_runner module."""
import pytest
from batchmark.priority import PriorityQueue
from batchmark.priority_runner import run_priority_queue
from batchmark.config import BenchmarkConfig


def make_config(concurrency: int = 2) -> BenchmarkConfig:
    return BenchmarkConfig(concurrency=concurrency, job_count=1)


def noop_job():
    pass


def failing_job():
    raise RuntimeError("boom")


def test_run_all_succeed():
    pq = PriorityQueue()
    for i in range(4):
        pq.push(noop_job, priority=i, label=f"job-{i}")
    results = run_priority_queue(pq, make_config())
    assert len(results) == 4
    assert all(r.error is None for r in results)


def test_run_with_failure():
    pq = PriorityQueue()
    pq.push(noop_job, priority=0, label="ok")
    pq.push(failing_job, priority=1, label="bad")
    results = run_priority_queue(pq, make_config())
    errors = [r for r in results if r.error is not None]
    assert len(errors) == 1
    assert "boom" in errors[0].error


def test_results_sorted_by_index():
    pq = PriorityQueue()
    for i in range(5):
        pq.push(noop_job, priority=5 - i)
    results = run_priority_queue(pq, make_config(concurrency=3))
    assert [r.index for r in results] == list(range(5))


def test_empty_queue_returns_empty():
    pq = PriorityQueue()
    results = run_priority_queue(pq, make_config())
    assert results == []


def test_labels_preserved():
    pq = PriorityQueue()
    pq.push(noop_job, priority=0, label="alpha")
    results = run_priority_queue(pq, make_config())
    assert results[0].label == "alpha"
