"""Configuration helpers for concurrency limiting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json
import os


@dataclass
class ConcurrencyConfig:
    max_workers: int = 4
    queue_timeout: Optional[float] = None

    def validate(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if self.queue_timeout is not None and self.queue_timeout <= 0:
            raise ValueError("queue_timeout must be positive")


def load_concurrency_config(path: str) -> ConcurrencyConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = json.load(f)
    cfg = ConcurrencyConfig(
        max_workers=data.get("max_workers", 4),
        queue_timeout=data.get("queue_timeout"),
    )
    cfg.validate()
    return cfg


def describe_concurrency_config(cfg: ConcurrencyConfig) -> str:
    lines = [f"max_workers : {cfg.max_workers}"]
    if cfg.queue_timeout is not None:
        lines.append(f"queue_timeout: {cfg.queue_timeout}s")
    else:
        lines.append("queue_timeout: unlimited")
    return "\n".join(lines)
