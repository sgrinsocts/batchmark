"""Tests for the CLI entry point."""

import json
from pathlib import Path

import pytest
import yaml

from batchmark.cli import main


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    cfg = {
        "jobs": [
            {"name": "job1", "command": "echo hello"},
            {"name": "job2", "command": "echo world"},
        ],
        "concurrency": 2,
        "timeout": 30,
    }
    p = tmp_path / "bench.yaml"
    p.write_text(yaml.dump(cfg))
    return p


def test_main_text_output(config_file: Path, capsys):
    rc = main([str(config_file)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "job1" in captured.out
    assert "job2" in captured.out


def test_main_json_output(config_file: Path, capsys):
    rc = main([str(config_file), "--format", "json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "results" in data


def test_main_write_file(config_file: Path, tmp_path: Path):
    out = tmp_path / "report.txt"
    rc = main([str(config_file), "--output", str(out)])
    assert rc == 0
    assert out.exists()
    assert len(out.read_text()) > 0


def test_main_concurrency_override(config_file: Path, capsys):
    rc = main([str(config_file), "--concurrency", "1"])
    assert rc == 0


def test_main_missing_config(tmp_path: Path, capsys):
    rc = main([str(tmp_path / "nonexistent.yaml")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_main_failing_job(tmp_path: Path):
    cfg = {"jobs": [{"name": "bad", "command": "false"}], "concurrency": 1}
    p = tmp_path / "fail.yaml"
    p.write_text(yaml.dump(cfg))
    rc = main([str(p)])
    assert rc == 2
