"""Simple plugin loader for batchmark hooks."""
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List

from batchmark.hooks import HookRegistry


def load_plugin_module(path: str):
    """Load a Python file as a plugin module."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Plugin file not found: {path}")
    spec = importlib.util.spec_from_file_location(p.stem, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def register_plugins(paths: List[str], registry: HookRegistry) -> None:
    """Load each plugin path and call its register(registry) function if present."""
    for path in paths:
        mod = load_plugin_module(path)
        if hasattr(mod, "register"):
            mod.register(registry)
        else:
            raise AttributeError(f"Plugin '{path}' must define a register(registry) function")
