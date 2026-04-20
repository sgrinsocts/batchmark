"""Load and validate jitter configuration from a YAML file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from batchmark.jitter import JitterPolicy, JitterStrategy, make_jitter_policy

_VALID_STRATEGIES: tuple[JitterStrategy, ...] = ("none", "full", "equal", "decorrelated")


@dataclass
class JitterConfig:
    strategy: JitterStrategy = "none"
    max_seconds: float = 1.0
    seed: int | None = None

    def validate(self) -> None:
        if self.strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"Invalid jitter strategy {self.strategy!r}. "
                f"Choose from {_VALID_STRATEGIES}."
            )
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")

    def to_policy(self) -> JitterPolicy:
        return make_jitter_policy(
            strategy=self.strategy,
            max_seconds=self.max_seconds,
            seed=self.seed,
        )


def load_jitter_config(path: str | Path) -> JitterConfig:
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
    jitter_data = data.get("jitter", {})
    cfg = JitterConfig(
        strategy=jitter_data.get("strategy", "none"),
        max_seconds=float(jitter_data.get("max_seconds", 1.0)),
        seed=jitter_data.get("seed"),
    )
    cfg.validate()
    return cfg


def describe_jitter_config(cfg: JitterConfig) -> str:
    return (
        f"JitterConfig(strategy={cfg.strategy}, "
        f"max_seconds={cfg.max_seconds}, seed={cfg.seed})"
    )
