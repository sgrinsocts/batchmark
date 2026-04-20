"""Runner that re-executes jobs when watched files change."""
from __future__ import annotations
from typing import Callable, List, Optional

from batchmark.config import BenchmarkConfig
from batchmark.runner import JobResult, run_all
from batchmark.watcher import FileWatcher, make_watcher
from batchmark.watcher_config import WatcherConfig


def run_on_change(
    job: Callable[[int], None],
    config: BenchmarkConfig,
    watcher_cfg: WatcherConfig,
    max_triggers: int = 1,
) -> List[List[JobResult]]:
    """Run jobs once immediately, then re-run each time watched files change."""
    if not watcher_cfg.enabled or not watcher_cfg.paths:
        return [run_all(job, config)]

    watcher = make_watcher(watcher_cfg.paths, watcher_cfg.poll_interval)
    all_runs: List[List[JobResult]] = []
    triggers = 0

    # Initial run
    all_runs.append(run_all(job, config))

    def _on_change(path: str) -> None:
        nonlocal triggers
        if triggers < max_triggers:
            results = run_all(job, config)
            all_runs.append(results)
            triggers += 1

    watcher.on_change(_on_change)
    watcher.watch(rounds=max_triggers * 2)
    return all_runs
