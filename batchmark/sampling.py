"""Job sampling — run only a fraction of jobs for quick benchmarks."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, TypeVar

T = TypeVar("T")


@dataclass
class SamplingConfig:
    """Controls how jobs are sampled before execution."""

    rate: float = 1.0          # fraction of jobs to keep, 0 < rate <= 1
    seed: Optional[int] = None # random seed for reproducibility
    min_jobs: int = 1          # always run at least this many jobs

    def __post_init__(self) -> None:
        if not (0 < self.rate <= 1.0):
            raise ValueError(f"rate must be in (0, 1], got {self.rate}")
        if self.min_jobs < 0:
            raise ValueError(f"min_jobs must be >= 0, got {self.min_jobs}")


def sample_jobs(
    jobs: Sequence[Callable],
    config: SamplingConfig,
) -> List[Callable]:
    """Return a sampled subset of *jobs* according to *config*."""
    if config.rate == 1.0:
        return list(jobs)

    rng = random.Random(config.seed)
    selected = [j for j in jobs if rng.random() < config.rate]

    # honour min_jobs guarantee
    if len(selected) < config.min_jobs and len(jobs) >= config.min_jobs:
        pool = [j for j in jobs if j not in selected]
        rng.shuffle(pool)
        selected += pool[: config.min_jobs - len(selected)]

    return selected


def make_sampling_config(
    rate: float = 1.0,
    seed: Optional[int] = None,
    min_jobs: int = 1,
) -> SamplingConfig:
    """Convenience constructor with validation."""
    return SamplingConfig(rate=rate, seed=seed, min_jobs=min_jobs)


def describe_sampling_config(cfg: SamplingConfig) -> str:
    """Return a human-readable description of the sampling configuration."""
    if cfg.rate == 1.0:
        return "sampling: disabled (all jobs run)"
    seed_str = f", seed={cfg.seed}" if cfg.seed is not None else ""
    return (
        f"sampling: {cfg.rate * 100:.1f}% of jobs"
        f" (min_jobs={cfg.min_jobs}{seed_str})"
    )
