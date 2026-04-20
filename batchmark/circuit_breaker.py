"""Circuit breaker pattern for protecting batch jobs from cascading failures."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking calls after too many failures
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)
    _half_open_calls: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def is_open(self) -> bool:
        return self.state is CircuitState.OPEN

    def allow_request(self) -> bool:
        s = self.state
        if s is CircuitState.CLOSED:
            return True
        if s is CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        return False

    def record_success(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
        self._failure_count = 0

    def record_failure(self) -> None:
        if self._state is CircuitState.HALF_OPEN:
            self._trip()
            return
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._trip()

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()
        self._failure_count = 0

    def reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = 0.0
        self._half_open_calls = 0


def make_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 1,
) -> CircuitBreaker:
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
    )
