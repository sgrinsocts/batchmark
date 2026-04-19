"""Tests for batchmark.dependency."""
import pytest
from batchmark.dependency import DependencyGraph, make_dependent_job


def noop():
    return "ok"


def test_make_dependent_job_defaults():
    j = make_dependent_job("a", noop)
    assert j.name == "a"
    assert j.depends_on == []
    assert j() == "ok"


def test_make_dependent_job_with_deps():
    j = make_dependent_job("b", noop, depends_on=["a"])
    assert j.depends_on == ["a"]


def test_add_and_get():
    g = DependencyGraph()
    j = make_dependent_job("a", noop)
    g.add(j)
    assert g.get("a") is j


def test_add_duplicate_raises():
    g = DependencyGraph()
    g.add(make_dependent_job("a", noop))
    with pytest.raises(ValueError, match="already registered"):
        g.add(make_dependent_job("a", noop))


def test_get_missing_raises():
    g = DependencyGraph()
    with pytest.raises(KeyError):
        g.get("missing")


def test_topological_order_no_deps():
    g = DependencyGraph()
    g.add(make_dependent_job("a", noop))
    g.add(make_dependent_job("b", noop))
    order = g.topological_order()
    assert set(order) == {"a", "b"}


def test_topological_order_respects_deps():
    g = DependencyGraph()
    g.add(make_dependent_job("a", noop))
    g.add(make_dependent_job("b", noop, depends_on=["a"]))
    g.add(make_dependent_job("c", noop, depends_on=["b"]))
    order = g.topological_order()
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_topological_order_cycle_raises():
    g = DependencyGraph()
    g.add(make_dependent_job("a", noop, depends_on=["b"]))
    g.add(make_dependent_job("b", noop, depends_on=["a"]))
    with pytest.raises(ValueError, match="Cycle"):
        g.topological_order()


def test_topological_order_unknown_dep_raises():
    g = DependencyGraph()
    g.add(make_dependent_job("a", noop, depends_on=["ghost"]))
    with pytest.raises(ValueError, match="Unknown dependency"):
        g.topological_order()


def test_names_returns_all():
    g = DependencyGraph()
    g.add(make_dependent_job("x", noop))
    g.add(make_dependent_job("y", noop))
    assert set(g.names()) == {"x", "y"}
