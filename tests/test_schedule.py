"""Tests for batchmark.schedule."""
import time
import pytest
from batchmark.schedule import (
    ScheduledJob,
    make_scheduled_job,
    filter_ready,
    filter_expired,
)


def noop():
    pass


def test_job_ready_immediately():
    job = make_scheduled_job(noop, delay=0.0)
    assert job.is_ready()


def test_job_not_ready_before_delay():
    job = make_scheduled_job(noop, delay=60.0)
    assert not job.is_ready()


def test_job_not_expired_no_deadline():
    job = make_scheduled_job(noop)
    assert not job.is_expired()


def test_job_expired_after_deadline(monkeypatch):
    start = time.monotonic()
    monkeypatch.setattr("batchmark.schedule.time.monotonic", lambda: start + 5.0)
    job = ScheduledJob(fn=noop, deadline=3.0)
    # Override _scheduled_at to simulate creation in the past
    object.__setattr__(job, "_scheduled_at", start)
    assert job.is_expired()


def test_make_scheduled_job_negative_delay_raises():
    with pytest.raises(ValueError, match="delay"):
        make_scheduled_job(noop, delay=-1.0)


def test_make_scheduled_job_zero_deadline_raises():
    with pytest.raises(ValueError, match="deadline"):
        make_scheduled_job(noop, deadline=0.0)


def test_make_scheduled_job_negative_deadline_raises():
    with pytest.raises(ValueError, match="deadline"):
        make_scheduled_job(noop, deadline=-5.0)


def test_filter_ready_returns_ready_jobs():
    ready = make_scheduled_job(noop, delay=0.0, label="ready")
    not_ready = make_scheduled_job(noop, delay=999.0, label="not_ready")
    result = filter_ready([ready, not_ready])
    assert len(result) == 1
    assert result[0].label == "ready"


def test_filter_expired_empty_when_no_deadlines():
    jobs = [make_scheduled_job(noop) for _ in range(3)]
    assert filter_expired(jobs) == []


def test_wait_until_ready_no_delay():
    job = make_scheduled_job(noop, delay=0.0)
    t0 = time.monotonic()
    job.wait_until_ready()
    assert (time.monotonic() - t0) < 0.1


def test_label_stored():
    job = make_scheduled_job(noop, label="my-job")
    assert job.label == "my-job"
