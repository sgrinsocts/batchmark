"""Checkpoint support for saving and resuming batch job progress."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Checkpoint:
    path: Path
    completed: Dict[str, float] = field(default_factory=dict)  # job_id -> timestamp
    failed: Dict[str, str] = field(default_factory=dict)       # job_id -> error

    def mark_complete(self, job_id: str) -> None:
        self.completed[job_id] = time.time()
        self.failed.pop(job_id, None)

    def mark_failed(self, job_id: str, error: str) -> None:
        self.failed[job_id] = error

    def is_complete(self, job_id: str) -> bool:
        return job_id in self.completed

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "completed": self.completed,
            "failed": self.failed,
        }
        self.path.write_text(json.dumps(data, indent=2))

    def pending(self, all_ids: List[str]) -> List[str]:
        return [jid for jid in all_ids if not self.is_complete(jid)]


def load_checkpoint(path: os.PathLike) -> Checkpoint:
    p = Path(path)
    if not p.exists():
        return Checkpoint(path=p)
    data = json.loads(p.read_text())
    return Checkpoint(
        path=p,
        completed=data.get("completed", {}),
        failed=data.get("failed", {}),
    )


def clear_checkpoint(path: os.PathLike) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
