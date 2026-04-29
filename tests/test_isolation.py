"""Tests for batchmark.isolation."""

import threading
import pytest

from batchmark.isolation import (
    IsolationPolicy,
    make_isolation_policy,
    describe_isolation_policy,
)


def test_default_policy_disabled():
    policy = IsolationPolicy()
    assert policy.enabled is False
    assert policy.copy_context is True
    assert policy.context_factory is None


def test_policy_enabled_when_flag_set():
    policy = IsolationPolicy(enabled=True)
    assert policy.enabled is True


def test_policy_invalid_context_factory_raises():
    with pytest.raises(ValueError, match="callable"):
        IsolationPolicy(enabled=True, context_factory="not-a-callable")  # type: ignore


def test_isolate_disabled_yields_without_local():
    policy = IsolationPolicy(enabled=False)
    with policy.isolate() as ctx:
        assert ctx is None


def test_isolate_enabled_yields_thread_local():
    policy = IsolationPolicy(enabled=True)
    with policy.isolate() as ctx:
        assert isinstance(ctx, threading.local)


def test_isolate_with_context_factory():
    def factory():
        return {"job_id": 42, "env": "test"}

    policy = IsolationPolicy(enabled=True, context_factory=factory)
    with policy.isolate() as ctx:
        assert ctx.job_id == 42
        assert ctx.env == "test"


def test_isolate_clears_context_after_exit():
    captured = {}

    def factory():
        return {"key": "value"}

    policy = IsolationPolicy(enabled=True, context_factory=factory)
    with policy.isolate() as ctx:
        captured["local"] = ctx
    assert len(captured["local"].__dict__) == 0


def test_make_isolation_policy_returns_instance():
    policy = make_isolation_policy(enabled=True, copy_context=False)
    assert isinstance(policy, IsolationPolicy)
    assert policy.enabled is True
    assert policy.copy_context is False


def test_describe_disabled():
    policy = IsolationPolicy(enabled=False)
    assert describe_isolation_policy(policy) == "isolation disabled"


def test_describe_enabled_no_factory():
    policy = IsolationPolicy(enabled=True, copy_context=True)
    desc = describe_isolation_policy(policy)
    assert "isolation enabled" in desc
    assert "copy_context=true" in desc


def test_describe_enabled_with_factory():
    policy = IsolationPolicy(enabled=True, context_factory=lambda: {})
    desc = describe_isolation_policy(policy)
    assert "custom context_factory" in desc
