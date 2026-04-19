"""Configuration helpers for priority-based job queues."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PriorityConfig:
    default_priority: int = 5
    max_priority: int = 10
    min_priority: int = 0

    def validate(self) -> None:
        if not (self.min_priority <= self.default_priority <= self.max_priority):
            raise ValueError(
                f"default_priority {self.default_priority} must be between "
                f"{self.min_priority} and {self.max_priority}"
            )
        if self.min_priority > self.max_priority:
            raise ValueError("min_priority must be <= max_priority")

    def clamp(self, priority: int) -> int:
        """Clamp a priority value to the allowed range."""
        return max(self.min_priority, min(self.max_priority, priority))


def load_priority_config(data: Dict[str, Any]) -> PriorityConfig:
    cfg = PriorityConfig(
        default_priority=data.get("default_priority", 5),
        max_priority=data.get("max_priority", 10),
        min_priority=data.get("min_priority", 0),
    )
    cfg.validate()
    return cfg


def describe_priority_config(cfg: PriorityConfig) -> str:
    return (
        f"Priority range [{cfg.min_priority}, {cfg.max_priority}], "
        f"default={cfg.default_priority}"
    )
