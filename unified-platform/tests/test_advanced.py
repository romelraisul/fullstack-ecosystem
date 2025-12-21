import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from workflow_engine import WorkflowEngine, WorkflowCycleError
from rag_engine import RAGEngine

def test_topological_sort_success():
    engine = WorkflowEngine(None)
    spec = {
        "steps": [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["B"]}
        ]
    }
    sorted_steps = engine.resolve_dependencies(spec)
    assert [s["id"] for s in sorted_steps] == ["A", "B", "C"]

def test_topological_sort_cycle():
    engine = WorkflowEngine(None)
    spec = {
        "steps": [
            {"id": "A", "depends_on": ["B"]},
            {"id": "B", "depends_on": ["A"]}
        ]
    }
    with pytest.raises(WorkflowCycleError):
        engine.resolve_dependencies(spec)

def test_rag_search():
    engine = RAGEngine()
    engine.add_documents([
        {"id": "1", "content": "FastAPI is a modern web framework."},
        {"id": "2", "content": "Python is a programming language."}
    ])
    
    results = engine.search("web framework")
    assert len(results) > 0
    assert "FastAPI" in results[0]["doc"]["content"]
    assert results[0]["score"] > 0
