"""Configuration loader for WavefrontPolicy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from batchmark.wavefront import WavefrontPolicy, make_wavefront_policy


@dataclass
class WavefrontConfig:
    max_in_flight: int = 0
    acquire_timeout: float = 5.0

    def validate(self) -> None:
        if self.max_in_flight < 0:
            raise ValueError("max_in_flight must be >= 0")
        if self.acquire_timeout < 0:
            raise ValueError("acquire_timeout must be >= 0")

    def to_policy(self) -> WavefrontPolicy:
        self.validate()
        return make_wavefront_policy(
            max_in_flight=self.max_in_flight,
            acquire_timeout=self.acquire_timeout,
        )

    def is_limited(self) -> bool:
        return self.max_in_flight > 0


def load_wavefront_config(path: str | Path) -> WavefrontConfig:
    data: Dict[str, Any] = json.loads(Path(path).read_text())
    cfg = WavefrontConfig(
        max_in_flight=int(data.get("max_in_flight", 0)),
        acquire_timeout=float(data.get("acquire_timeout", 5.0)),
    )
    cfg.validate()
    return cfg


def describe_wavefront_config(cfg: WavefrontConfig) -> str:
    if not cfg.is_limited():
        return "wavefront config: unlimited"
    return (
        f"wavefront config: max_in_flight={cfg.max_in_flight}, "
        f"acquire_timeout={cfg.acquire_timeout}s"
    )
