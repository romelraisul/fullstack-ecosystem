import pytest

from autogen.advanced_backend import resolve_step_order


def test_resolve_linear():
    steps = [
        {"name": "a", "agent_id": "x", "depends_on": []},
        {"name": "b", "agent_id": "x", "depends_on": ["a"]},
        {"name": "c", "agent_id": "x", "depends_on": ["b"]},
    ]
    order = resolve_step_order(steps)
    assert order == ["a", "b", "c"]


def test_resolve_branch():
    steps = [
        {"name": "a", "agent_id": "x", "depends_on": []},
        {"name": "b", "agent_id": "x", "depends_on": ["a"]},
        {"name": "c", "agent_id": "x", "depends_on": ["a"]},
        {"name": "d", "agent_id": "x", "depends_on": ["b", "c"]},
    ]
    order = resolve_step_order(steps)
    assert order[0] == "a"
    assert order[-1] == "d"
    assert set(order) == {"a", "b", "c", "d"}


def test_cycle_detection():
    steps = [
        {"name": "a", "agent_id": "x", "depends_on": ["c"]},
        {"name": "b", "agent_id": "x", "depends_on": ["a"]},
        {"name": "c", "agent_id": "x", "depends_on": ["b"]},
    ]
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        resolve_step_order(steps)
