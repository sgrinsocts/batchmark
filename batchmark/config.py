"""Configuration loading and validation for batchmark."""

from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class BenchmarkConfig:
    concurrency: int = 1
    total_jobs: int = 10
    timeout: float = 30.0
    output_format: str = "table"  # table | json | csv
    report_file: Optional[str] = None
    job_command: str = ""
    labels: dict = field(default_factory=dict)

    def validate(self):
        errors = []
        if self.concurrency < 1:
            errors.append("concurrency must be >= 1")
        if self.total_jobs < 1:
            errors.append("total_jobs must be >= 1")
        if self.timeout <= 0:
            errors.append("timeout must be > 0")
        if self.output_format not in ("table", "json", "csv"):
            errors.append(f"output_format must be one of: table, json, csv")
        if not self.job_command:
            errors.append("job_command must not be empty")
        if errors:
            raise ValueError("Invalid config:\n" + "\n".join(f"  - {e}" for e in errors))


def load_config(path: str) -> BenchmarkConfig:
    """Load a BenchmarkConfig from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        data = json.load(f)
    cfg = BenchmarkConfig(
        concurrency=data.get("concurrency", 1),
        total_jobs=data.get("total_jobs", 10),
        timeout=data.get("timeout", 30.0),
        output_format=data.get("output_format", "table"),
        report_file=data.get("report_file"),
        job_command=data.get("job_command", ""),
        labels=data.get("labels", {}),
    )
    cfg.validate()
    return cfg
