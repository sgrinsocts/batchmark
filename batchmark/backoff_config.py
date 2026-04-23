"""Configuration loader for BackoffPolicy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from batchmark.backoff import BackoffPolicy, make_backoff_policy


@dataclass
class BackoffConfig:
    strategy: str = "exponential"
    base: float = 1.0
    factor: float = 2.0
    max_delay: float = 60.0

    def validate(self) -> None:
        from batchmark.backoff import VALID_STRATEGIES
        if self.strategy not in VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy '{self.strategy}'.")
        if self.base < 0:
            raise ValueError("base must be non-negative.")
        if self.factor <= 0:
            raise ValueError("factor must be positive.")
        if self.max_delay < 0:
            raise ValueError("max_delay must be non-negative.")

    def to_policy(self) -> BackoffPolicy:
        self.validate()
        return make_backoff_policy(
            strategy=self.strategy,
            base=self.base,
            factor=self.factor,
            max_delay=self.max_delay,
        )


def load_backoff_config(path: str | Path) -> BackoffConfig:
    data: dict[str, Any] = json.loads(Path(path).read_text())
    backoff_data = data.get("backoff", {})
    cfg = BackoffConfig(
        strategy=backoff_data.get("strategy", "exponential"),
        base=float(backoff_data.get("base", 1.0)),
        factor=float(backoff_data.get("factor", 2.0)),
        max_delay=float(backoff_data.get("max_delay", 60.0)),
    )
    cfg.validate()
    return cfg


def describe_backoff_config(cfg: BackoffConfig) -> str:
    return (
        f"BackoffConfig(strategy={cfg.strategy}, base={cfg.base}, "
        f"factor={cfg.factor}, max_delay={cfg.max_delay})"
    )
