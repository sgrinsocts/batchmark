"""Tests for batchmark.priority module."""
import pytest
from batchmark.priority import PrioritizedJob, PriorityQueue, make_priority_queue


def noop():
    return "ok"


def test_push_and_pop_order():
    pq = PriorityQueue()
    pq.push(noop, priority=3, label="c")
    pq.push(noop, priority=1, label="a")
    pq.push(noop, priority=2, label="b")
    assert pq.pop().label == "a"
    assert pq.pop().label == "b"
    assert pq.pop().label == "c"


def test_pop_empty_raises():
    pq = PriorityQueue()
    with pytest.raises(IndexError):
        pq.pop()


def test_peek_does_not_remove():
    pq = PriorityQueue()
    pq.push(noop, priority=1)
    pq.peek()
    assert len(pq) == 1


def test_peek_empty_raises():
    pq = PriorityQueue()
    with pytest.raises(IndexError):
        pq.peek()


def test_bool_empty():
    pq = PriorityQueue()
    assert not pq
    pq.push(noop)
    assert pq


def test_drain_returns_ordered_and_empties():
    pq = PriorityQueue()
    pq.push(noop, priority=10)
    pq.push(noop, priority=0)
    pq.push(noop, priority=5)
    drained = pq.drain()
    assert [j.priority for j in drained] == [0, 5, 10]
    assert len(pq) == 0


def test_prioritized_job_callable():
    results = []
    pq = PriorityQueue()
    pq.push(lambda: results.append(1), priority=0)
    job = pq.pop()
    job()
    assert results == [1]


def test_make_priority_queue_two_tuple():
    pq = make_priority_queue([(2, noop), (1, noop)])
    assert pq.pop().priority == 1


def test_make_priority_queue_three_tuple():
    pq = make_priority_queue([(1, noop, "first"), (0, noop, "zero")])
    assert pq.pop().label == "zero"
