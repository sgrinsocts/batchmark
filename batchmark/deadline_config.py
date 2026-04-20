"""Load and validate deadline configuration from a TOML file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from batchmark.deadline import DeadlinePolicy, make_deadline_policy


@dataclass
class DeadlineConfig:
    seconds: float = 0.0
    grace_period: float = 0.0

    def validate(self) -> None:
        if self.seconds < 0:
            raise ValueError("deadline.seconds must be >= 0")
        if self.grace_period < 0:
            raise ValueError("deadline.grace_period must be >= 0")

    def to_policy(self) -> DeadlinePolicy:
        self.validate()
        return make_deadline_policy(
            seconds=self.seconds,
            grace_period=self.grace_period,
        )

    @property
    def is_limited(self) -> bool:
        return self.seconds > 0


def load_deadline_config(path: str | Path) -> DeadlineConfig:
    """Load a [deadline] section from a TOML config file."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    section = raw.get("deadline", {})
    cfg = DeadlineConfig(
        seconds=float(section.get("seconds", 0.0)),
        grace_period=float(section.get("grace_period", 0.0)),
    )
    cfg.validate()
    return cfg


def describe_deadline_config(cfg: DeadlineConfig) -> str:
    if not cfg.is_limited:
        return "deadline: none"
    parts = [f"deadline.seconds={cfg.seconds}"]
    if cfg.grace_period:
        parts.append(f"grace_period={cfg.grace_period}")
    return ", ".join(parts)
