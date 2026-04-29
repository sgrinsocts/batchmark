"""Load and describe BurstPolicy from a TOML/dict config."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from batchmark.burst import BurstPolicy, describe_burst_policy, make_burst_policy

try:
    import tomllib
except ImportError:  # Python < 3.11
    import tomli as tomllib  # type: ignore


_DEFAULTS: Dict[str, Any] = {
    "strategy": "none",
    "steady_rate": 0.0,
    "burst_size": 0,
    "window_seconds": 1.0,
}


@dataclass_like = None  # not a dataclass; plain helper functions


def validate(cfg: Dict[str, Any]) -> None:
    """Raise ValueError for invalid burst config values."""
    strategy = cfg.get("strategy", _DEFAULTS["strategy"])
    if strategy not in {"token_bucket", "none"}:
        raise ValueError(f"burst.strategy must be 'token_bucket' or 'none', got {strategy!r}")
    steady_rate = cfg.get("steady_rate", _DEFAULTS["steady_rate"])
    if steady_rate < 0:
        raise ValueError("burst.steady_rate must be >= 0")
    burst_size = cfg.get("burst_size", _DEFAULTS["burst_size"])
    if burst_size < 0:
        raise ValueError("burst.burst_size must be >= 0")
    window_seconds = cfg.get("window_seconds", _DEFAULTS["window_seconds"])
    if window_seconds <= 0:
        raise ValueError("burst.window_seconds must be > 0")


def to_policy(cfg: Dict[str, Any]) -> BurstPolicy:
    """Convert a config dict to a BurstPolicy."""
    validate(cfg)
    return make_burst_policy(
        strategy=cfg.get("strategy", _DEFAULTS["strategy"]),
        steady_rate=float(cfg.get("steady_rate", _DEFAULTS["steady_rate"])),
        burst_size=int(cfg.get("burst_size", _DEFAULTS["burst_size"])),
        window_seconds=float(cfg.get("window_seconds", _DEFAULTS["window_seconds"])),
    )


def is_active(cfg: Dict[str, Any]) -> bool:
    """Return True if the burst policy would be enabled."""
    return (
        cfg.get("strategy", _DEFAULTS["strategy"]) != "none"
        and float(cfg.get("steady_rate", 0.0)) > 0
    )


def load_burst_config(path: str | Path) -> BurstPolicy:
    """Load a TOML file and return a BurstPolicy from its [burst] section."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    section = raw.get("burst", {})
    return to_policy(section)


def describe_burst_config(path: str | Path) -> str:
    policy = load_burst_config(path)
    return describe_burst_policy(policy)
