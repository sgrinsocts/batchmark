"""Extended formatting helpers that include metrics output."""

from __future__ import annotations

import json
from typing import Optional

from batchmark.metrics import MetricsSummary


def format_metrics_text(summary: MetricsSummary) -> str:
    lines = [
        "=== Metrics Summary ===",
        f"Total jobs      : {summary.total}",
        f"Succeeded       : {summary.succeeded}",
        f"Failed          : {summary.failed}",
        f"Success rate    : {summary.success_rate:.1%}",
        "",
        "Duration (seconds):",
        f"  Min           : {summary.min_duration:.4f}",
        f"  Max           : {summary.max_duration:.4f}",
        f"  Mean          : {summary.mean_duration:.4f}",
        f"  Std dev       : {summary.stddev_duration:.4f}",
        "",
        "Percentiles:",
        f"  p50           : {summary.percentiles.p50:.4f}",
        f"  p90           : {summary.percentiles.p90:.4f}",
        f"  p95           : {summary.percentiles.p95:.4f}",
        f"  p99           : {summary.percentiles.p99:.4f}",
    ]
    if summary.error_types:
        lines.append("")
        lines.append("Error types:")
        for etype, count in summary.error_types.items():
            lines.append(f"  {etype}: {count}")
    return "\n".join(lines)


def format_metrics_json(summary: MetricsSummary) -> str:
    data = {
        "total": summary.total,
        "succeeded": summary.succeeded,
        "failed": summary.failed,
        "success_rate": round(summary.success_rate, 6),
        "duration": {
            "min": summary.min_duration,
            "max": summary.max_duration,
            "mean": summary.mean_duration,
            "stddev": summary.stddev_duration,
            "percentiles": {
                "p50": summary.percentiles.p50,
                "p90": summary.percentiles.p90,
                "p95": summary.percentiles.p95,
                "p99": summary.percentiles.p99,
            },
        },
        "error_types": summary.error_types,
    }
    return json.dumps(data, indent=2)
