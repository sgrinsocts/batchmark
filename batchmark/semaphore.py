"""Async semaphore wrapper for controlling concurrent job execution slots."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any


@dataclass
class SemaphorePolicy:
    max_slots: int = 0  # 0 = unlimited
    timeout: float = 0.0  # 0 = wait forever

    def __post_init__(self) -> None:
        if self.max_slots < 0:
            raise ValueError("max_slots must be >= 0")
        if self.timeout < 0:
            raise ValueError("timeout must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.max_slots > 0


def make_semaphore_policy(max_slots: int = 0, timeout: float = 0.0) -> SemaphorePolicy:
    return SemaphorePolicy(max_slots=max_slots, timeout=timeout)


def describe_semaphore_policy(policy: SemaphorePolicy) -> str:
    if not policy.enabled:
        return "semaphore: unlimited slots"
    parts = [f"semaphore: max_slots={policy.max_slots}"]
    if policy.timeout > 0:
        parts.append(f"timeout={policy.timeout}s")
    return ", ".join(parts)


async def run_with_semaphore(
    policy: SemaphorePolicy,
    jobs: list[Callable[[], Awaitable[Any]]],
) -> list[Any]:
    """Run async jobs constrained by the semaphore policy."""
    if not policy.enabled:
        return [await job() for job in jobs]

    sem = asyncio.Semaphore(policy.max_slots)
    results: list[Any] = []

    async def _acquire_and_run(job: Callable[[], Awaitable[Any]]) -> Any:
        if policy.timeout > 0:
            try:
                acquired = await asyncio.wait_for(
                    sem.acquire(), timeout=policy.timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Could not acquire semaphore slot within {policy.timeout}s"
                )
        else:
            await sem.acquire()
        try:
            return await job()
        finally:
            sem.release()

    tasks = [asyncio.create_task(_acquire_and_run(j)) for j in jobs]
    for task in tasks:
        results.append(await task)
    return results
