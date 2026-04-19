"""Budget-related config helpers."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from batchmark.budget import TimeBudget, make_budget


@dataclass
class BudgetConfig:
    """Optional time budget settings loaded from config."""
    max_seconds: Optional[float] = None

    def to_budget(self) -> Optional[TimeBudget]:
        return make_budget(self.max_seconds)


def load_budget_config(raw: dict) -> BudgetConfig:
    """Parse budget section from a raw config dict."""
    budget_raw = raw.get("budget", {})
    max_seconds = budget_raw.get("max_seconds", None)
    if max_seconds is not None:
        max_seconds = float(max_seconds)
    return BudgetConfig(max_seconds=max_seconds)


def describe_budget(budget: Optional[TimeBudget]) -> str:
    """Return a human-readable description of the budget."""
    if budget is None:
        return "no time budget"
    return f"time budget: {budget.max_seconds:.1f}s (remaining: {budget.remaining():.1f}s)"
