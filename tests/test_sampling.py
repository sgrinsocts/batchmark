"""Tests for batchmark.sampling."""
import pytest

from batchmark.sampling import (
    SamplingConfig,
    describe_sampling_config,
    make_sampling_config,
    sample_jobs,
)


def noop(idx: int):
    return lambda: idx


JOBS = [noop(i) for i in range(20)]


# ---------------------------------------------------------------------------
# SamplingConfig validation
# ---------------------------------------------------------------------------

def test_default_config_is_valid():
    cfg = SamplingConfig()
    assert cfg.rate == 1.0
    assert cfg.seed is None
    assert cfg.min_jobs == 1


def test_invalid_rate_zero():
    with pytest.raises(ValueError, match="rate"):
        SamplingConfig(rate=0.0)


def test_invalid_rate_above_one():
    with pytest.raises(ValueError, match="rate"):
        SamplingConfig(rate=1.1)


def test_invalid_min_jobs():
    with pytest.raises(ValueError, match="min_jobs"):
        SamplingConfig(min_jobs=-1)


# ---------------------------------------------------------------------------
# sample_jobs behaviour
# ---------------------------------------------------------------------------

def test_rate_one_returns_all():
    cfg = make_sampling_config(rate=1.0)
    result = sample_jobs(JOBS, cfg)
    assert result == list(JOBS)


def test_sample_reduces_job_count():
    cfg = make_sampling_config(rate=0.3, seed=42)
    result = sample_jobs(JOBS, cfg)
    assert len(result) < len(JOBS)


def test_sample_reproducible_with_seed():
    cfg = make_sampling_config(rate=0.5, seed=7)
    r1 = sample_jobs(JOBS, cfg)
    r2 = sample_jobs(JOBS, cfg)
    assert [id(j) for j in r1] == [id(j) for j in r2]


def test_min_jobs_respected_when_rate_is_low():
    cfg = make_sampling_config(rate=0.01, seed=0, min_jobs=5)
    result = sample_jobs(JOBS, cfg)
    assert len(result) >= 5


def test_empty_job_list_returns_empty():
    cfg = make_sampling_config(rate=0.5, seed=1)
    assert sample_jobs([], cfg) == []


# ---------------------------------------------------------------------------
# describe_sampling_config
# ---------------------------------------------------------------------------

def test_describe_disabled():
    cfg = make_sampling_config(rate=1.0)
    desc = describe_sampling_config(cfg)
    assert "disabled" in desc


def test_describe_enabled_shows_percent():
    cfg = make_sampling_config(rate=0.25, seed=99)
    desc = describe_sampling_config(cfg)
    assert "25.0%" in desc
    assert "seed=99" in desc


def test_describe_no_seed_omits_seed():
    cfg = make_sampling_config(rate=0.5)
    desc = describe_sampling_config(cfg)
    assert "seed" not in desc
