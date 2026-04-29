"""Load and validate spillover configuration from a TOML/dict source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from batchmark.spillover import SpilloverPolicy, make_spillover_policy


@dataclass
class SpilloverConfig:
    enabled: bool = False
    threshold: int = 0
    max_spilled: int = 0

    def validate(self) -> None:
        if self.threshold < 0:
            raise ValueError("spillover.threshold must be >= 0")
        if self.max_spilled < 0:
            raise ValueError("spillover.max_spilled must be >= 0")

    def to_policy(self) -> SpilloverPolicy:
        self.validate()
        return make_spillover_policy(
            threshold=self.threshold,
            max_spilled=self.max_spilled,
            enabled=self.enabled,
        )

    def is_active(self) -> bool:
        return self.enabled


def load_spillover_config(data: Dict[str, Any]) -> SpilloverConfig:
    section = data.get("spillover", {})
    cfg = SpilloverConfig(
        enabled=bool(section.get("enabled", False)),
        threshold=int(section.get("threshold", 0)),
        max_spilled=int(section.get("max_spilled", 0)),
    )
    cfg.validate()
    return cfg


def describe_spillover_config(cfg: SpilloverConfig) -> str:
    if not cfg.enabled:
        return "spillover config: disabled"
    return (
        f"spillover config: enabled, threshold={cfg.threshold}, "
        f"max_spilled={cfg.max_spilled}"
    )
