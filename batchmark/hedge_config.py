"""Configuration loader for HedgePolicy."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from batchmark.hedge import HedgePolicy, make_hedge_policy


@dataclass
class HedgeConfig:
    enabled: bool = False
    delay_seconds: float = 0.5
    max_hedges: int = 1

    def validate(self) -> None:
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        if self.max_hedges < 1:
            raise ValueError("max_hedges must be >= 1")

    def to_policy(self) -> HedgePolicy:
        self.validate()
        return make_hedge_policy(
            delay_seconds=self.delay_seconds,
            max_hedges=self.max_hedges,
            enabled=self.enabled,
        )

    def is_limited(self) -> bool:
        return self.enabled


def load_hedge_config(path: str | Path) -> HedgeConfig:
    data: Dict[str, Any] = json.loads(Path(path).read_text())
    hedge_data = data.get("hedge", {})
    cfg = HedgeConfig(
        enabled=hedge_data.get("enabled", False),
        delay_seconds=float(hedge_data.get("delay_seconds", 0.5)),
        max_hedges=int(hedge_data.get("max_hedges", 1)),
    )
    cfg.validate()
    return cfg


def describe_hedge_config(cfg: HedgeConfig) -> str:
    if not cfg.enabled:
        return "hedge config: disabled"
    return (
        f"hedge config: enabled, delay={cfg.delay_seconds}s, "
        f"max_hedges={cfg.max_hedges}"
    )
