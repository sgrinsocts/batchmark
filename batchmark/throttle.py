"""Rate limiting / throttle utilities for batchmark."""

import time
import threading
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Token-bucket rate limiter.

    Args:
        rate: maximum calls per second (0 = unlimited)
    """

    rate: float  # calls per second
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _tokens: float = field(init=False, repr=False)
    _last: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._tokens = float(self.rate) if self.rate > 0 else 0.0
        self._last = time.monotonic()

    def acquire(self) -> None:
        """Block until a token is available."""
        if self.rate <= 0:
            return
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self.rate, self._tokens + elapsed * self.rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            wait = (1.0 - self._tokens) / self.rate
            self._tokens = 0.0
        time.sleep(wait)

    def __call__(self) -> None:
        self.acquire()

    @property
    def interval(self) -> float:
        """Minimum seconds between calls (0 if unlimited)."""
        return 1.0 / self.rate if self.rate > 0 else 0.0


def make_rate_limiter(rate: float) -> RateLimiter:
    """Factory that returns a RateLimiter for *rate* calls/sec."""
    if rate < 0:
        raise ValueError(f"rate must be >= 0, got {rate}")
    return RateLimiter(rate=rate)
