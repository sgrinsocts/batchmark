"""Tests for batchmark.labels."""
import pytest
from batchmark.labels import (
    LabeledJob,
    make_labeled_job,
    filter_by_labels,
    group_by_label,
)


def noop():
    pass


def test_make_labeled_job():
    job = make_labeled_job(noop, "j1", env="prod", team="data")
    assert job.name == "j1"
    assert job.get("env") == "prod"
    assert job.get("team") == "data"
    assert job.get("missing") is None


def test_call_delegates_to_job():
    called = []
    job = make_labeled_job(lambda: called.append(1), "j")
    job()
    assert called == [1]


def test_matches_all_selector_keys():
    job = make_labeled_job(noop, "j", env="prod", region="us")
    assert job.matches({"env": "prod"})
    assert job.matches({"env": "prod", "region": "us"})
    assert not job.matches({"env": "staging"})
    assert not job.matches({"env": "prod", "region": "eu"})


def test_matches_empty_selector_always_true():
    """An empty selector should match any job regardless of its labels."""
    job = make_labeled_job(noop, "j", env="prod")
    assert job.matches({})

    unlabeled_job = make_labeled_job(noop, "k")
    assert unlabeled_job.matches({})


def test_filter_by_labels_returns_matching():
    jobs = [
        make_labeled_job(noop, "a", env="prod"),
        make_labeled_job(noop, "b", env="staging"),
        make_labeled_job(noop, "c", env="prod"),
    ]
    result = filter_by_labels(jobs, {"env": "prod"})
    assert [j.name for j in result] == ["a", "c"]


def test_filter_by_labels_empty_selector_returns_all():
    jobs = [make_labeled_job(noop, "a"), make_labeled_job(noop, "b")]
    assert filter_by_labels(jobs, {}) == jobs


def test_filter_by_labels_no_matches_returns_empty():
    """filter_by_labels should return an empty list when no jobs match."""
    jobs = [
        make_labeled_job(noop, "a", env="prod"),
        make_labeled_job(noop, "b", env="staging"),
    ]
    result = filter_by_labels(jobs, {"env": "canary"})
    assert result == []


def test_group_by_label_groups_correctly():
    jobs = [
        make_labeled_job(noop, "a", env="prod"),
        make_labeled_job(noop, "b", env="staging"),
        make_labeled_job(noop, "c", env="prod"),
    ]
    groups = group_by_label(jobs, "env")
    assert set(groups.keys()) == {"prod", "staging"}
    assert [j.name for j in groups["prod"]] == ["a", "c"]
    assert [j.name for j in groups["staging"]] == ["b"]


def test_group_by_label_missing_key_uses_unlabeled():
    jobs = [
        make_labeled_job(noop, "a", env="prod"),
        make_labeled_job(noop, "b"),
    ]
    groups = group_by_label(jobs, "env")
    assert "__unlabeled__" in groups
    assert groups["__unlabeled__"][0].name == "b"
