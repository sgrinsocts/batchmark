"""Job quota enforcement — limit total jobs run per session."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobQuota:
    max_jobs: int
    _count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_jobs < 1:
            raise ValueError(f"max_jobs must be >= 1, got {self.max_jobs}")

    def increment(self) -> None:
        self._count += 1

    def is_exhausted(self) -> bool:
        return self._count >= self.max_jobs

    def remaining(self) -> int:
        return max(0, self.max_jobs - self._count)

    def reset(self) -> None:
        self._count = 0

    @property
    def count(self) -> int:
        return self._count


def make_quota(max_jobs: Optional[int]) -> Optional[JobQuota]:
    """Return a JobQuota if max_jobs is specified, else None."""
    if max_jobs is None:
        return None
    return JobQuota(max_jobs=max_jobs)


def check_quota(quota: Optional[JobQuota]) -> None:
    """Raise RuntimeError if quota is exhausted."""
    if quota is not None and quota.is_exhausted():
        raise RuntimeError(
            f"Job quota exhausted: limit was {quota.max_jobs}"
        )


def describe_quota(quota: Optional[JobQuota]) -> str:
    if quota is None:
        return "quota: unlimited"
    return f"quota: {quota.count}/{quota.max_jobs} used, {quota.remaining()} remaining"
