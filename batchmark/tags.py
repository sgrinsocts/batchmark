from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass
class TaggedJob:
    job: Callable
    tags: frozenset[str] = field(default_factory=frozenset)

    def __call__(self, *args, **kwargs):
        return self.job(*args, **kwargs)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def matches_any(self, tags: Iterable[str]) -> bool:
        return bool(self.tags & frozenset(tags))

    def matches_all(self, tags: Iterable[str]) -> bool:
        return frozenset(tags) <= self.tags


def make_tagged_job(job: Callable, tags: Iterable[str] = ()) -> TaggedJob:
    return TaggedJob(job=job, tags=frozenset(tags))


def filter_by_tag(jobs: Iterable[TaggedJob], tag: str) -> list[TaggedJob]:
    return [j for j in jobs if j.has_tag(tag)]


def filter_by_any(jobs: Iterable[TaggedJob], tags: Iterable[str]) -> list[TaggedJob]:
    tag_set = list(tags)
    return [j for j in jobs if j.matches_any(tag_set)]


def filter_by_all(jobs: Iterable[TaggedJob], tags: Iterable[str]) -> list[TaggedJob]:
    tag_set = list(tags)
    return [j for j in jobs if j.matches_all(tag_set)]


def group_by_tag(jobs: Iterable[TaggedJob]) -> dict[str, list[TaggedJob]]:
    groups: dict[str, list[TaggedJob]] = {}
    for job in jobs:
        for tag in job.tags:
            groups.setdefault(tag, []).append(job)
    return groups
