"""Load and describe timeout configuration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from batchmark.timeout import TimeoutPolicy, make_timeout_policy


@dataclass
class TimeoutConfig:
    seconds: Optional[float] = None

    def to_policy(self) -> TimeoutPolicy:
        return make_timeout_policy(self.seconds)

    def is_limited(self) -> bool:
        return self.seconds is not None


def load_timeout_config(data: Dict[str, Any]) -> TimeoutConfig:
    """Parse timeout section from a config dict."""
    section = data.get("timeout", {})
    seconds = section.get("seconds", None)
    if seconds is not None:
        seconds = float(seconds)
    return TimeoutConfig(seconds=seconds)


def describe_timeout_config(cfg: TimeoutConfig) -> str:
    if not cfg.is_limited():
        return "timeout: none"
    return f"timeout: {cfg.seconds}s per job"
