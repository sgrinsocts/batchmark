"""Tests for batchmark config loading and validation."""

import json
import os
import pytest
import tempfile

from batchmark.config import BenchmarkConfig, load_config


def write_config(data: dict) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


def test_default_config_valid():
    cfg = BenchmarkConfig(job_command="echo hello")
    cfg.validate()  # should not raise


def test_load_config_minimal():
    path = write_config({"job_command": "echo hi", "total_jobs": 5})
    try:
        cfg = load_config(path)
        assert cfg.job_command == "echo hi"
        assert cfg.total_jobs == 5
        assert cfg.concurrency == 1
        assert cfg.output_format == "table"
    finally:
        os.unlink(path)


def test_load_config_full():
    data = {
        "job_command": "sleep 0.1",
        "concurrency": 4,
        "total_jobs": 20,
        "timeout": 60.0,
        "output_format": "json",
        "report_file": "report.json",
        "labels": {"env": "ci"},
    }
    path = write_config(data)
    try:
        cfg = load_config(path)
        assert cfg.concurrency == 4
        assert cfg.labels == {"env": "ci"}
        assert cfg.report_file == "report.json"
    finally:
        os.unlink(path)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.json")


def test_invalid_concurrency():
    cfg = BenchmarkConfig(job_command="echo", concurrency=0)
    with pytest.raises(ValueError, match="concurrency"):
        cfg.validate()


def test_invalid_output_format():
    cfg = BenchmarkConfig(job_command="echo", output_format="xml")
    with pytest.raises(ValueError, match="output_format"):
        cfg.validate()


def test_empty_job_command():
    cfg = BenchmarkConfig(job_command="")
    with pytest.raises(ValueError, match="job_command"):
        cfg.validate()
