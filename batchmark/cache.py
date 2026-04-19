"""Simple in-memory result cache keyed by job identity."""
from __future__ import annotations
import hashlib
import json
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    key: str
    value: Any
    hits: int = 0


class ResultCache:
    """Thread-safe cache for job results."""

    def __init__(self, max_size: int = 256):
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def _make_key(self, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, payload: Any) -> tuple[bool, Any]:
        key = self._make_key(payload)
        with self._lock:
            entry = self._store.get(key)
            if entry is not None:
                entry.hits += 1
                return True, entry.value
        return False, None

    def set(self, payload: Any, value: Any) -> None:
        key = self._make_key(payload)
        with self._lock:
            if len(self._store) >= self._max_size and key not in self._store:
                # evict oldest
                oldest = next(iter(self._store))
                del self._store[oldest]
            self._store[key] = CacheEntry(key=key, value=value)

    def stats(self) -> dict:
        with self._lock:
            total_hits = sum(e.hits for e in self._store.values())
            return {"size": len(self._store), "total_hits": total_hits, "max_size": self._max_size}

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
