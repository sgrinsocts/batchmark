"""Job dependency graph — ensures jobs run only after their dependencies complete."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Set


@dataclass
class DependentJob:
    name: str
    job: Callable
    depends_on: List[str] = field(default_factory=list)

    def __call__(self, *args, **kwargs):
        return self.job(*args, **kwargs)


@dataclass
class DependencyGraph:
    _jobs: Dict[str, DependentJob] = field(default_factory=dict)

    def add(self, job: DependentJob) -> None:
        if job.name in self._jobs:
            raise ValueError(f"Job '{job.name}' already registered")
        self._jobs[job.name] = job

    def names(self) -> List[str]:
        return list(self._jobs.keys())

    def get(self, name: str) -> DependentJob:
        if name not in self._jobs:
            raise KeyError(f"Job '{name}' not found")
        return self._jobs[name]

    def topological_order(self) -> List[str]:
        visited: Set[str] = set()
        order: List[str] = []
        visiting: Set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise ValueError(f"Cycle detected involving job '{name}'")
            if name in visited:
                return
            visiting.add(name)
            job = self.get(name)
            for dep in job.depends_on:
                if dep not in self._jobs:
                    raise ValueError(f"Unknown dependency '{dep}' for job '{name}'")
                visit(dep)
            visiting.discard(name)
            visited.add(name)
            order.append(name)

        for name in self._jobs:
            visit(name)
        return order


def make_dependent_job(name: str, job: Callable, depends_on: List[str] | None = None) -> DependentJob:
    return DependentJob(name=name, job=job, depends_on=depends_on or [])
