"""Configuration loader for SemaphorePolicy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from batchmark.semaphore import SemaphorePolicy, make_semaphore_policy


@dataclass
class SemaphoreConfig:
    max_slots: int = 0
    timeout: float = 0.0

    def validate(self) -> None:
        if self.max_slots < 0:
            raise ValueError("max_slots must be >= 0")
        if self.timeout < 0:
            raise ValueError("timeout must be >= 0")

    def to_policy(self) -> SemaphorePolicy:
        self.validate()
        return make_semaphore_policy(
            max_slots=self.max_slots,
            timeout=self.timeout,
        )

    def is_limited(self) -> bool:
        return self.max_slots > 0


def load_semaphore_config(path: str | Path) -> SemaphoreConfig:
    data: dict[str, Any] = json.loads(Path(path).read_text())
    section = data.get("semaphore", {})
    cfg = SemaphoreConfig(
        max_slots=int(section.get("max_slots", 0)),
        timeout=float(section.get("timeout", 0.0)),
    )
    cfg.validate()
    return cfg


def describe_semaphore_config(cfg: SemaphoreConfig) -> str:
    if not cfg.is_limited():
        return "semaphore config: unlimited"
    parts = [f"max_slots={cfg.max_slots}"]
    if cfg.timeout > 0:
        parts.append(f"timeout={cfg.timeout}s")
    return "semaphore config: " + ", ".join(parts)
