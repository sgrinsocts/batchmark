"""Tests for batchmark.checkpoint."""

import pytest
from pathlib import Path

from batchmark.checkpoint import Checkpoint, load_checkpoint, clear_checkpoint


@pytest.fixture
def ckpt_path(tmp_path) -> Path:
    return tmp_path / "checkpoints" / "run.json"


def test_new_checkpoint_empty(ckpt_path):
    ckpt = load_checkpoint(ckpt_path)
    assert ckpt.completed == {}
    assert ckpt.failed == {}


def test_mark_complete(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_complete("job-1")
    assert ckpt.is_complete("job-1")
    assert "job-1" not in ckpt.failed


def test_mark_failed(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_failed("job-2", "timeout")
    assert not ckpt.is_complete("job-2")
    assert ckpt.failed["job-2"] == "timeout"


def test_mark_complete_clears_failed(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_failed("job-3", "error")
    ckpt.mark_complete("job-3")
    assert ckpt.is_complete("job-3")
    assert "job-3" not in ckpt.failed


def test_pending_excludes_completed(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_complete("job-1")
    result = ckpt.pending(["job-1", "job-2", "job-3"])
    assert result == ["job-2", "job-3"]


def test_save_and_reload(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_complete("job-A")
    ckpt.mark_failed("job-B", "oops")
    ckpt.save()

    loaded = load_checkpoint(ckpt_path)
    assert loaded.is_complete("job-A")
    assert loaded.failed["job-B"] == "oops"


def test_clear_checkpoint(ckpt_path):
    ckpt = Checkpoint(path=ckpt_path)
    ckpt.mark_complete("job-X")
    ckpt.save()
    assert ckpt_path.exists()

    clear_checkpoint(ckpt_path)
    assert not ckpt_path.exists()


def test_clear_nonexistent_checkpoint(ckpt_path):
    # Should not raise
    clear_checkpoint(ckpt_path)
