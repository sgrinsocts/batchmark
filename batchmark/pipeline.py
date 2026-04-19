"""High-level pipeline: run jobs, collect metrics, format and write report."""

from __future__ import annotations

from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.formatter import format_metrics_json, format_metrics_text
from batchmark.metrics import MetricsSummary, compute_metrics
from batchmark.runner import JobResult, run_all


def run_pipeline(
    config: BenchmarkConfig,
    job_fn: Callable,
    output_format: str = "text",
    output_path: Optional[str] = None,
) -> MetricsSummary:
    """Execute benchmark pipeline: run jobs, compute metrics, optionally write report."""
    results: List[JobResult] = run_all(config, job_fn)
    summary = compute_metrics(results)

    report = _format(summary, output_format)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(report)
    else:
        print(report)

    return summary


def _format(summary: MetricsSummary, fmt: str) -> str:
    if fmt == "json":
        return format_metrics_json(summary)
    return format_metrics_text(summary)
