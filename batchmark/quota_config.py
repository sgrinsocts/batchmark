"""Load and describe quota configuration from a dict or YAML section."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

from batchmark.quota import JobQuota, make_quota


@dataclass
class QuotaConfig:
    max_jobs: Optional[int] = None

    def to_quota(self) -> Optional[JobQuota]:
        return make_quota(self.max_jobs)

    def is_limited(self) -> bool:
        """Return True if a job limit is configured."""
        return self.max_jobs is not None

    def merge(self, other: "QuotaConfig") -> "QuotaConfig":
        """Return a new QuotaConfig combining this config with *other*.

        Values from *other* take precedence over this instance when set.

        Args:
            other: Another :class:`QuotaConfig` whose values override.

        Returns:
            A new :class:`QuotaConfig` with merged values.
        """
        return QuotaConfig(
            max_jobs=other.max_jobs if other.max_jobs is not None else self.max_jobs,
        )


def load_quota_config(data: Dict[str, Any]) -> QuotaConfig:
    """Parse a quota configuration from a config mapping.

    Expects an optional ``quota`` key whose value is a mapping.  Supported
    fields inside that mapping:

    - ``max_jobs`` (int, optional): maximum number of jobs allowed per run.
      Must be >= 1 if provided.

    Args:
        data: Top-level configuration dictionary.

    Returns:
        A :class:`QuotaConfig` instance.

    Raises:
        ValueError: If ``quota`` is not a mapping or ``max_jobs`` is invalid.
    """
    raw = data.get("quota", {})
    if not isinstance(raw, dict):
        raise ValueError("'quota' section must be a mapping")
    max_jobs = raw.get("max_jobs", None)
    if max_jobs is not None:
        max_jobs = int(max_jobs)
        if max_jobs < 1:
            raise ValueError(f"quota.max_jobs must be >= 1, got {max_jobs}")
    return QuotaConfig(max_jobs=max_jobs)


def describe_quota_config(cfg: QuotaConfig) -> str:
    if cfg.max_jobs is None:
        return "Quota: unlimited"
    return f"Quota: max {cfg.max_jobs} jobs per run"
