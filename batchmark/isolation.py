"""Isolation policy for running jobs in separate execution contexts."""

from __future__ import annotations

import contextlib
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class IsolationPolicy:
    """Controls whether each job runs in an isolated thread-local context."""

    enabled: bool = False
    copy_context: bool = True
    context_factory: Optional[Callable[[], Dict[str, Any]]] = None

    def __post_init__(self) -> None:
        if self.context_factory is not None and not callable(self.context_factory):
            raise ValueError("context_factory must be callable")

    @contextlib.contextmanager
    def isolate(self):
        """Context manager that sets up an isolated thread-local environment."""
        if not self.enabled:
            yield
            return

        local = threading.local()
        if self.context_factory is not None:
            ctx = self.context_factory()
            for k, v in ctx.items():
                setattr(local, k, v)
        try:
            yield local
        finally:
            local.__dict__.clear()

    def describe(self) -> str:
        if not self.enabled:
            return "isolation disabled"
        parts = ["isolation enabled"]
        if self.copy_context:
            parts.append("copy_context=true")
        if self.context_factory is not None:
            parts.append("custom context_factory")
        return ", ".join(parts)


def make_isolation_policy(
    enabled: bool = False,
    copy_context: bool = True,
    context_factory: Optional[Callable[[], Dict[str, Any]]] = None,
) -> IsolationPolicy:
    return IsolationPolicy(
        enabled=enabled,
        copy_context=copy_context,
        context_factory=context_factory,
    )


def describe_isolation_policy(policy: IsolationPolicy) -> str:
    return policy.describe()
