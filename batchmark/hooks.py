"""Lifecycle hooks for benchmark pipeline events."""
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from batchmark.metrics import MetricsSummary


HookFn = Callable[..., None]


@dataclass
class HookRegistry:
    """Registry of callbacks for pipeline lifecycle events."""
    on_start: List[HookFn] = field(default_factory=list)
    on_job_complete: List[HookFn] = field(default_factory=list)
    on_finish: List[HookFn] = field(default_factory=list)

    def register_start(self, fn: HookFn) -> None:
        self.on_start.append(fn)

    def register_job_complete(self, fn: HookFn) -> None:
        self.on_job_complete.append(fn)

    def register_finish(self, fn: HookFn) -> None:
        self.on_finish.append(fn)

    def fire_start(self, config) -> None:
        for fn in self.on_start:
            fn(config)

    def fire_job_complete(self, result) -> None:
        for fn in self.on_job_complete:
            fn(result)

    def fire_finish(self, summary: MetricsSummary) -> None:
        for fn in self.on_finish:
            fn(summary)


_default_registry: Optional[HookRegistry] = None


def get_registry() -> HookRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = HookRegistry()
    return _default_registry


def reset_registry() -> None:
    global _default_registry
    _default_registry = None
