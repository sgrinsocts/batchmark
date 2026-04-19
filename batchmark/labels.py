"""Label-based filtering and grouping for batch jobs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

Job = Callable[[], None]


@dataclass
class LabeledJob:
    job: Job
    name: str
    labels: Dict[str, str] = field(default_factory=dict)

    def __call__(self):
        return self.job()

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def matches(self, selector: Dict[str, str]) -> bool:
        """Return True if all selector key/value pairs are present in labels."""
        return all(self.labels.get(k) == v for k, v in selector.items())


def make_labeled_job(job: Job, name: str, **labels: str) -> LabeledJob:
    return LabeledJob(job=job, name=name, labels=dict(labels))


def filter_by_labels(jobs: List[LabeledJob], selector: Dict[str, str]) -> List[LabeledJob]:
    """Return jobs whose labels match all key/value pairs in selector."""
    return [j for j in jobs if j.matches(selector)]


def group_by_label(jobs: List[LabeledJob], key: str) -> Dict[str, List[LabeledJob]]:
    """Group jobs by the value of a given label key."""
    groups: Dict[str, List[LabeledJob]] = {}
    for job in jobs:
        value = job.get(key) or "__unlabeled__"
        groups.setdefault(value, []).append(job)
    return groups
