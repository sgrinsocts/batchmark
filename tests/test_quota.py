"""Tests for batchmark.quota."""
import pytest
from batchmark.quota import JobQuota, make_quota, check_quota, describe_quota


def test_quota_initial_count():
    q = JobQuota(max_jobs=5)
    assert q.count == 0
    assert q.remaining() == 5
    assert not q.is_exhausted()


def test_quota_increment():
    q = JobQuota(max_jobs=3)
    q.increment()
    q.increment()
    assert q.count == 2
    assert q.remaining() == 1
    assert not q.is_exhausted()


def test_quota_exhausted():
    q = JobQuota(max_jobs=2)
    q.increment()
    q.increment()
    assert q.is_exhausted()
    assert q.remaining() == 0


def test_quota_reset():
    q = JobQuota(max_jobs=2)
    q.increment()
    q.reset()
    assert q.count == 0
    assert not q.is_exhausted()


def test_quota_invalid():
    with pytest.raises(ValueError):
        JobQuota(max_jobs=0)


def test_make_quota_none():
    assert make_quota(None) is None


def test_make_quota_value():
    q = make_quota(10)
    assert q is not None
    assert q.max_jobs == 10


def test_check_quota_none_ok():
    check_quota(None)  # should not raise


def test_check_quota_not_exhausted_ok():
    q = JobQuota(max_jobs=5)
    check_quota(q)  # should not raise


def test_check_quota_exhausted_raises():
    q = JobQuota(max_jobs=1)
    q.increment()
    with pytest.raises(RuntimeError, match="exhausted"):
        check_quota(q)


def test_describe_quota_unlimited():
    assert "unlimited" in describe_quota(None)


def test_describe_quota_with_quota():
    q = JobQuota(max_jobs=10)
    q.increment()
    desc = describe_quota(q)
    assert "1/10" in desc
    assert "9" in desc
