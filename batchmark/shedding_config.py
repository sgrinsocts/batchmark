"""Configuration loader for SheddingPolicy."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from batchmark.shedding import SheddingPolicy, make_shedding_policy


@dataclass
class SheddingConfig:
    enabled: bool = False
    max_queue_depth: int = 0
    load_threshold: float = 1.0
    sample_window: float = 5.0

    def validate(self) -> None:
        if self.max_queue_depth < 0:
            raise ValueError("max_queue_depth must be >= 0")
        if not (0.0 < self.load_threshold <= 1.0):
            raise ValueError("load_threshold must be in (0.0, 1.0]")
        if self.sample_window <= 0:
            raise ValueError("sample_window must be > 0")

    def to_policy(self) -> SheddingPolicy:
        self.validate()
        return make_shedding_policy(
            enabled=self.enabled,
            max_queue_depth=self.max_queue_depth,
            load_threshold=self.load_threshold,
            sample_window=self.sample_window,
        )

    def is_active(self) -> bool:
        return self.enabled


def load_shedding_config(path: str | Path) -> SheddingConfig:
    """Load a SheddingConfig from a JSON file."""
    data: Dict[str, Any] = json.loads(Path(path).read_text())
    cfg = SheddingConfig(
        enabled=data.get("enabled", False),
        max_queue_depth=data.get("max_queue_depth", 0),
        load_threshold=data.get("load_threshold", 1.0),
        sample_window=data.get("sample_window", 5.0),
    )
    cfg.validate()
    return cfg


def describe_shedding_config(cfg: SheddingConfig) -> str:
    if not cfg.enabled:
        return "shedding config: disabled"
    return (
        f"shedding config: enabled, threshold={cfg.load_threshold:.0%}, "
        f"max_queue={cfg.max_queue_depth}, window={cfg.sample_window}s"
    )
