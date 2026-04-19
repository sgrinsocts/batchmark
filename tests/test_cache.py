"""Tests for batchmark.cache."""
import pytest
from batchmark.cache import ResultCache


def test_cache_miss():
    c = ResultCache()
    hit, val = c.get({"job": "a"})
    assert not hit
    assert val is None


def test_cache_hit_after_set():
    c = ResultCache()
    c.set({"job": "a"}, "result")
    hit, val = c.get({"job": "a"})
    assert hit
    assert val == "result"


def test_cache_key_order_independent():
    c = ResultCache()
    c.set({"b": 2, "a": 1}, "x")
    hit, val = c.get({"a": 1, "b": 2})
    assert hit
    assert val == "x"


def test_cache_hit_increments_counter():
    c = ResultCache()
    c.set("k", 99)
    c.get("k")
    c.get("k")
    stats = c.stats()
    assert stats["total_hits"] == 2


def test_cache_miss_does_not_increment_hit_counter():
    c = ResultCache()
    c.get("nonexistent")
    c.get("also_missing")
    stats = c.stats()
    assert stats["total_hits"] == 0


def test_cache_evicts_when_full():
    c = ResultCache(max_size=2)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)  # should evict "a"
    assert c.stats()["size"] == 2
    hit, _ = c.get("a")
    assert not hit


def test_cache_clear():
    c = ResultCache()
    c.set("x", 1)
    c.clear()
    assert c.stats()["size"] == 0


def test_cache_clear_resets_hit_counter():
    c = ResultCache()
    c.set("x", 1)
    c.get("x")
    c.clear()
    assert c.stats()["total_hits"] == 0


def test_cache_invalid_max_size():
    with pytest.raises(ValueError):
        ResultCache(max_size=0)


def test_cache_stats_structure():
    c = ResultCache(max_size=10)
    c.set("a", 1)
    s = c.stats()
    assert "size" in s
    assert "total_hits" in s
    assert s["max_size"] == 10
