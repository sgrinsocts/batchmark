"""Tests for batchmark.formatter extended metrics formatting."""

import json
import pytest
from batchmark.formatter import format_metrics_json, format_metrics_text
from batchmark.metrics import MetricsSummary, PercentileStats


def make_summary(**kwargs) -> MetricsSummary:
    defaults = dict(
        total=10,
        succeeded=8,
        failed=2,
        min_duration=0.05,
        max_duration=1.20,
        mean_duration=0.45,
        stddev_duration=0.30,
        percentiles=PercentileStats(p50=0.40, p90=0.90, p95=1.00, p99=1.15),
        error_types={"RuntimeError": 2},
    )
    defaults.update(kwargs)
    return MetricsSummary(**defaults)


def test_format_metrics_text_contains_key_fields():
    summary = make_summary()
    text = format_metrics_text(summary)
    assert "Total jobs" in text
    assert "80.0%" in text
    assert "p50" in text
    assert "RuntimeError" in text


def test_format_metrics_text_no_errors_section():
    summary = make_summary(error_types={})
    text = format_metrics_text(summary)
    assert "Error types" not in text


def test_format_metrics_json_valid():
    summary = make_summary()
    raw = format_metrics_json(summary)
    data = json.loads(raw)
    assert data["total"] == 10
    assert data["succeeded"] == 8
    assert data["failed"] == 2
    assert abs(data["success_rate"] - 0.8) < 1e-6
    assert "percentiles" in data["duration"]
    assert data["error_types"]["RuntimeError"] == 2


def test_format_metrics_json_percentiles():
    summary = make_summary()
    data = json.loads(format_metrics_json(summary))
    p = data["duration"]["percentiles"]
    assert p["p50"] == 0.40
    assert p["p99"] == 1.15
