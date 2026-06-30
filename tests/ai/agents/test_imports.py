"""Agent import tests — parameterized for maintainability.

Consolidated from 5 standalone test functions into 1 parameterized test.
"""

import pytest

# All agent classes that should be importable
_AGENT_CLASSES = [
    ("ai.agents.base.base_agent", "BaseAgent"),
    ("ai.agents.specialized.audio_processing_agent", "AudioProcessingAgent"),
    ("ai.agents.specialized.code_understanding_agent", "CodeUnderstandingAgent"),
    ("ai.agents.specialized.creative_writing_agent", "CreativeWritingAgent"),
    ("ai.agents.specialized.data_analysis_agent", "DataAnalysisAgent"),
    ("ai.agents.specialized.knowledge_graph_agent", "KnowledgeGraphAgent"),
]


@pytest.mark.parametrize("module_path,class_name", _AGENT_CLASSES)
def test_agent_import(module_path: str, class_name: str) -> None:
    """Verify each agent class can be imported."""
    import importlib

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    assert cls is not None, f"{module_path}.{class_name} not found"
