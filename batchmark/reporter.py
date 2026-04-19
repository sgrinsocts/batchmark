"""Report generation for benchmark run summaries."""

import json
from typing import IO

from batchmark.runner import RunSummary


def format_text(summary: RunSummary) -> str:
    lines = [
        "=== Benchmark Report ===",
        f"Total jobs    : {summary.total}",
        f"Succeeded     : {summary.succeeded}",
        f"Failed        : {summary.failed}",
        f"Success rate  : {summary.success_rate:.1%}",
        f"Total duration: {summary.total_duration:.4f}s",
        f"Avg duration  : {summary.avg_duration:.4f}s",
    ]
    if summary.failed:
        lines.append("\nFailed jobs:")
        for r in summary.results:
            if not r.success:
                lines.append(f"  [{r.job_id}] {r.error}")
    return "\n".join(lines)


def format_json(summary: RunSummary) -> str:
    data = {
        "total": summary.total,
        "succeeded": summary.succeeded,
        "failed": summary.failed,
        "success_rate": round(summary.success_rate, 4),
        "total_duration": round(summary.total_duration, 6),
        "avg_duration": round(summary.avg_duration, 6),
        "results": [
            {
                "job_id": r.job_id,
                "success": r.success,
                "duration": round(r.duration, 6),
                "error": r.error,
            }
            for r in summary.results
        ],
    }
    return json.dumps(data, indent=2)


def write_report(summary: RunSummary, fmt: str = "text", stream: IO = None) -> str:
    """Write report to stream (or return as string)."""
    if fmt == "json":
        output = format_json(summary)
    else:
        output = format_text(summary)

    if stream is not None:
        stream.write(output + "\n")
    return output
