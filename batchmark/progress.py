"""Progress tracking for benchmark runs."""
import sys
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProgressTracker:
    total: int
    completed: int = 0
    failed: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    silent: bool = False

    def record(self, success: bool) -> None:
        with self._lock:
            self.completed += 1
            if not success:
                self.failed += 1
            if not self.silent:
                self._render()

    def _render(self) -> None:
        pct = int(self.completed / self.total * 100) if self.total else 0
        bar_len = 30
        filled = int(bar_len * self.completed / self.total) if self.total else 0
        bar = "#" * filled + "-" * (bar_len - filled)
        line = f"\r[{bar}] {pct}%  {self.completed}/{self.total}  failed={self.failed}"
        sys.stderr.write(line)
        sys.stderr.flush()
        if self.completed == self.total:
            sys.stderr.write("\n")
            sys.stderr.flush()

    @property
    def success_count(self) -> int:
        return self.completed - self.failed
