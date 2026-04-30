"""Configuration loader for WindowPolicy."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from batchmark.window import WindowPolicy, make_window_policy


@dataclass
class WindowConfig:
    max_calls: int = 0
    window_seconds: float = 1.0

    def validate(self) -> None:
        if self.max_calls < 0:
            raise ValueError("max_calls must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    def to_policy(self) -> WindowPolicy:
        self.validate()
        return make_window_policy(
            max_calls=self.max_calls,
            window_seconds=self.window_seconds,
        )

    def is_active(self) -> bool:
        return self.max_calls > 0


def load_window_config(path: str | Path) -> WindowConfig:
    data: Dict[str, Any] = json.loads(Path(path).read_text())
    cfg = WindowConfig(
        max_calls=int(data.get("max_calls", 0)),
        window_seconds=float(data.get("window_seconds", 1.0)),
    )
    cfg.validate()
    return cfg


def describe_window_config(cfg: WindowConfig) -> str:
    if not cfg.is_active():
        return "window config: unlimited"
    return (
        f"window config: {cfg.max_calls} calls / {cfg.window_seconds:.2f}s window"
    )
