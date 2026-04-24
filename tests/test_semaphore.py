"""Tests for batchmark.semaphore and batchmark.semaphore_config."""

from __future__ import annotations

import asyncio
import json
import pytest
from pathlib import Path

from batchmark.semaphore import (
    SemaphorePolicy,
    make_semaphore_policy,
    describe_semaphore_policy,
    run_with_semaphore,
)
from batchmark.semaphore_config import (
    SemaphoreConfig,
    load_semaphore_config,
    describe_semaphore_config,
)


# --- SemaphorePolicy ---

def test_default_policy_disabled():
    p = SemaphorePolicy()
    assert not p.enabled
    assert p.max_slots == 0


def test_policy_enabled_when_slots_positive():
    p = make_semaphore_policy(max_slots=4)
    assert p.enabled


def test_policy_invalid_negative_slots():
    with pytest.raises(ValueError, match="max_slots"):
        SemaphorePolicy(max_slots=-1)


def test_policy_invalid_negative_timeout():
    with pytest.raises(ValueError, match="timeout"):
        SemaphorePolicy(max_slots=2, timeout=-0.5)


def test_describe_unlimited():
    p = make_semaphore_policy()
    assert "unlimited" in describe_semaphore_policy(p)


def test_describe_limited():
    p = make_semaphore_policy(max_slots=3, timeout=1.0)
    desc = describe_semaphore_policy(p)
    assert "3" in desc
    assert "1.0" in desc


# --- run_with_semaphore ---

def test_run_unlimited_returns_all():
    async def _run():
        async def job():
            return 42
        results = await run_with_semaphore(make_semaphore_policy(), [job, job, job])
        assert results == [42, 42, 42]
    asyncio.run(_run())


def test_run_with_slots_returns_all():
    async def _run():
        counter = [0]
        async def job():
            counter[0] += 1
            return counter[0]
        policy = make_semaphore_policy(max_slots=2)
        results = await run_with_semaphore(policy, [job] * 5)
        assert len(results) == 5
    asyncio.run(_run())


def test_run_timeout_raises_on_deadlock():
    async def _run():
        barrier = asyncio.Event()
        async def blocking_job():
            await barrier.wait()
        policy = make_semaphore_policy(max_slots=1, timeout=0.05)
        with pytest.raises(TimeoutError):
            await run_with_semaphore(policy, [blocking_job, blocking_job])
    asyncio.run(_run())


# --- SemaphoreConfig ---

def test_semaphore_config_defaults():
    cfg = SemaphoreConfig()
    assert not cfg.is_limited()


def test_semaphore_config_to_policy():
    cfg = SemaphoreConfig(max_slots=5, timeout=2.0)
    p = cfg.to_policy()
    assert isinstance(p, SemaphorePolicy)
    assert p.max_slots == 5


def test_load_semaphore_config(tmp_path: Path):
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps({"semaphore": {"max_slots": 8, "timeout": 1.5}}))
    cfg = load_semaphore_config(cfg_file)
    assert cfg.max_slots == 8
    assert cfg.timeout == 1.5


def test_load_semaphore_config_missing_section(tmp_path: Path):
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps({}))
    cfg = load_semaphore_config(cfg_file)
    assert cfg.max_slots == 0


def test_describe_semaphore_config_unlimited():
    cfg = SemaphoreConfig()
    assert "unlimited" in describe_semaphore_config(cfg)


def test_describe_semaphore_config_limited():
    cfg = SemaphoreConfig(max_slots=4)
    assert "4" in describe_semaphore_config(cfg)
