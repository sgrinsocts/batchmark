"""Tests for plugin loader."""
import pytest
from pathlib import Path
from batchmark.hooks import HookRegistry
from batchmark.plugin import load_plugin_module, register_plugins


VALID_PLUGIN = """
calls = []
def register(registry):
    registry.register_start(lambda cfg: calls.append(cfg))
"""

BAD_PLUGIN = "x = 1\n"


@pytest.fixture
def plugin_file(tmp_path):
    p = tmp_path / "myplugin.py"
    p.write_text(VALID_PLUGIN)
    return str(p)


@pytest.fixture
def bad_plugin_file(tmp_path):
    p = tmp_path / "badplugin.py"
    p.write_text(BAD_PLUGIN)
    return str(p)


def test_load_plugin_module(plugin_file):
    mod = load_plugin_module(plugin_file)
    assert hasattr(mod, "register")


def test_load_plugin_missing():
    with pytest.raises(FileNotFoundError):
        load_plugin_module("/nonexistent/plugin.py")


def test_register_plugins_fires_hook(plugin_file):
    reg = HookRegistry()
    register_plugins([plugin_file], reg)
    reg.fire_start("cfg")
    mod = load_plugin_module(plugin_file)
    # hook was registered; verify registry has one on_start entry
    assert len(reg.on_start) == 1


def test_register_plugins_bad_plugin(bad_plugin_file):
    reg = HookRegistry()
    with pytest.raises(AttributeError, match="register"):
        register_plugins([bad_plugin_file], reg)
