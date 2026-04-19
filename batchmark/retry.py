"""Retry logic for batch jobs with configurable backoff."""
from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_attempts: int = 1
    backoff_base: float = 0.5
    backoff_max: float = 10.0
    exceptions: tuple = field(default_factory=lambda: (Exception,))

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.backoff_base < 0:
            raise ValueError("backoff_base must be >= 0")

    def delay(self, attempt: int) -> float:
        """Exponential backoff delay for a given attempt (0-indexed)."""
        return min(self.backoff_base * (2 ** attempt), self.backoff_max)


def with_retry(fn: Callable, policy: RetryPolicy, *args, **kwargs) -> Any:
    """Call fn with retry according to policy. Raises last exception on exhaustion."""
    last_exc: Exception | None = None
    for attempt in range(policy.max_attempts):
        try:
            return fn(*args, **kwargs)
        except policy.exceptions as exc:
            last_exc = exc
            if attempt < policy.max_attempts - 1:
                delay = policy.delay(attempt)
                logger.debug("Retry %d/%d after %.2fs: %s", attempt + 1, policy.max_attempts, delay, exc)
                time.sleep(delay)
    raise last_exc


def make_retry_policy(cfg: dict) -> RetryPolicy:
    """Build a RetryPolicy from a config dict (e.g. loaded from TOML)."""
    return RetryPolicy(
        max_attempts=cfg.get("max_attempts", 1),
        backoff_base=cfg.get("backoff_base", 0.5),
        backoff_max=cfg.get("backoff_max", 10.0),
    )
