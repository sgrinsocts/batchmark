"""File watcher that triggers job reruns when watched paths change."""
from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class WatchedPath:
    path: str
    last_mtime: float = 0.0

    def has_changed(self) -> bool:
        try:
            mtime = os.path.getmtime(self.path)
        except FileNotFoundError:
            return False
        if mtime != self.last_mtime:
            self.last_mtime = mtime
            return True
        return False

    def sync(self) -> None:
        try:
            self.last_mtime = os.path.getmtime(self.path)
        except FileNotFoundError:
            self.last_mtime = 0.0


@dataclass
class FileWatcher:
    paths: List[WatchedPath] = field(default_factory=list)
    poll_interval: float = 1.0
    _on_change: Optional[Callable[[str], None]] = field(default=None, repr=False)

    def add(self, path: str) -> None:
        wp = WatchedPath(path=path)
        wp.sync()
        self.paths.append(wp)

    def on_change(self, fn: Callable[[str], None]) -> None:
        self._on_change = fn

    def check_once(self) -> List[str]:
        changed = []
        for wp in self.paths:
            if wp.has_changed():
                changed.append(wp.path)
                if self._on_change:
                    self._on_change(wp.path)
        return changed

    def watch(self, rounds: int = -1) -> None:
        count = 0
        while rounds < 0 or count < rounds:
            self.check_once()
            time.sleep(self.poll_interval)
            count += 1


def make_watcher(paths: List[str], poll_interval: float = 1.0) -> FileWatcher:
    fw = FileWatcher(poll_interval=poll_interval)
    for p in paths:
        fw.add(p)
    return fw
