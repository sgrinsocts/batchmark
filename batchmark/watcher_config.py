"""Configuration for the file watcher feature."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class WatcherConfig:
    paths: List[str] = field(default_factory=list)
    poll_interval: float = 1.0
    enabled: bool = True

    def validate(self) -> None:
        if self.poll_interval <= 0:
            raise ValueError(f"poll_interval must be positive, got {self.poll_interval}")
        for p in self.paths:
            if not isinstance(p, str) or not p:
                raise ValueError(f"Invalid path entry: {p!r}")


def load_watcher_config(path: str) -> WatcherConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = json.load(f)
    cfg = WatcherConfig(
        paths=data.get("paths", []),
        poll_interval=data.get("poll_interval", 1.0),
        enabled=data.get("enabled", True),
    )
    cfg.validate()
    return cfg


def describe_watcher_config(cfg: WatcherConfig) -> str:
    status = "enabled" if cfg.enabled else "disabled"
    return (
        f"FileWatcher({status}): watching {len(cfg.paths)} path(s) "
        f"every {cfg.poll_interval}s"
    )
