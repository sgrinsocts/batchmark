"""Tests for batchmark.watcher and batchmark.watcher_config."""
import json
import os
import time
import pytest

from batchmark.watcher import WatchedPath, FileWatcher, make_watcher
from batchmark.watcher_config import WatcherConfig, load_watcher_config, describe_watcher_config


def test_watched_path_no_file_no_change(tmp_path):
    wp = WatchedPath(path=str(tmp_path / "missing.txt"))
    assert not wp.has_changed()


def test_watched_path_detects_change(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("hello")
    wp = WatchedPath(path=str(p))
    wp.sync()
    time.sleep(0.05)
    p.write_text("world")
    os.utime(str(p), (time.time() + 1, time.time() + 1))
    assert wp.has_changed()


def test_make_watcher_adds_paths(tmp_path):
    p1 = tmp_path / "a.txt"
    p2 = tmp_path / "b.txt"
    p1.write_text("a")
    p2.write_text("b")
    fw = make_watcher([str(p1), str(p2)], poll_interval=0.1)
    assert len(fw.paths) == 2


def test_check_once_returns_changed(tmp_path):
    p = tmp_path / "watch.txt"
    p.write_text("v1")
    fw = make_watcher([str(p)], poll_interval=0.1)
    os.utime(str(p), (time.time() + 2, time.time() + 2))
    changed = fw.check_once()
    assert str(p) in changed


def test_on_change_callback_called(tmp_path):
    p = tmp_path / "cb.txt"
    p.write_text("x")
    fw = make_watcher([str(p)], poll_interval=0.1)
    seen = []
    fw.on_change(lambda path: seen.append(path))
    os.utime(str(p), (time.time() + 2, time.time() + 2))
    fw.check_once()
    assert str(p) in seen


def test_watcher_config_validate_bad_interval():
    cfg = WatcherConfig(paths=["a.txt"], poll_interval=-1.0)
    with pytest.raises(ValueError, match="poll_interval"):
        cfg.validate()


def test_load_watcher_config(tmp_path):
    cfg_file = tmp_path / "watcher.json"
    cfg_file.write_text(json.dumps({"paths": ["a.txt"], "poll_interval": 0.5}))
    cfg = load_watcher_config(str(cfg_file))
    assert cfg.poll_interval == 0.5
    assert cfg.paths == ["a.txt"]


def test_load_watcher_config_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_watcher_config(str(tmp_path / "nope.json"))


def test_describe_watcher_config():
    cfg = WatcherConfig(paths=["a", "b"], poll_interval=2.0, enabled=True)
    desc = describe_watcher_config(cfg)
    assert "2" in desc
    assert "enabled" in desc
