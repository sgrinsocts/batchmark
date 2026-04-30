"""Configuration for rate limiting / throttling."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from batchmark.throttle import RateLimiter, make_rate_limiter


@dataclass
class ThrottleConfig:
    enabled: bool = False
    rate: float = 0.0          # calls per second; 0 means unlimited
    burst: int = 1             # ignored when rate == 0
    description: str = ""

    def validate(self) -> None:
        if self.rate < 0:
            raise ValueError(f"rate must be >= 0, got {self.rate}")
        if self.burst < 1:
            raise ValueError(f"burst must be >= 1, got {self.burst}")

    def to_limiter(self) -> RateLimiter:
        if not self.enabled or self.rate == 0.0:
            return make_rate_limiter(0.0)
        return make_rate_limiter(self.rate)

    def is_active(self) -> bool:
        return self.enabled and self.rate > 0


def load_throttle_config(path: str | Path) -> ThrottleConfig:
    data = json.loads(Path(path).read_text())
    cfg = ThrottleConfig(
        enabled=data.get("enabled", False),
        rate=float(data.get("rate", 0.0)),
        burst=int(data.get("burst", 1)),
        description=data.get("description", ""),
    )
    cfg.validate()
    return cfg


def describe_throttle_config(cfg: ThrottleConfig) -> str:
    if not cfg.is_active():
        return "throttle: disabled (unlimited throughput)"
    return f"throttle: {cfg.rate:.2f} calls/sec (burst={cfg.burst})"
