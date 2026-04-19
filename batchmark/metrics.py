"""Metrics collection and aggregation for benchmark runs."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List, Optional

from batchmark.runner import JobResult


@dataclass
class PercentileStats:
    p50: float
    p90: float
    p95: float
    p99: float


@dataclass
class MetricsSummary:
    total: int
    succeeded: int
    failed: int
    min_duration: float
    max_duration: float
    mean_duration: float
    stddev_duration: float
    percentiles: PercentileStats
    error_types: dict = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        return self.succeeded / self.total if self.total else 0.0


def compute_percentiles(durations: List[float]) -> PercentileStats:
    if not durations:
        return PercentileStats(0.0, 0.0, 0.0, 0.0)
    s = sorted(durations)
    def pct(p):
        idx = int(len(s) * p / 100)
        return s[min(idx, len(s) - 1)]
    return PercentileStats(
        p50=pct(50), p90=pct(90), p95=pct(95), p99=pct(99)
    )


def collect_error_types(results: List[JobResult]) -> dict:
    counts: dict = {}
    for r in results:
        if r.error:
            key = type(r.error).__name__
            counts[key] = counts.get(key, 0) + 1
    return counts


def compute_metrics(results: List[JobResult]) -> MetricsSummary:
    if not results:
        raise ValueError("No results to compute metrics from.")

    durations = [r.duration for r in results]
    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    stddev = statistics.stdev(durations) if len(durations) > 1 else 0.0

    return MetricsSummary(
        total=len(results),
        succeeded=len(succeeded),
        failed=len(failed),
        min_duration=min(durations),
        max_duration=max(durations),
        mean_duration=statistics.mean(durations),
        stddev_duration=stddev,
        percentiles=compute_percentiles(durations),
        error_types=collect_error_types(results),
    )
