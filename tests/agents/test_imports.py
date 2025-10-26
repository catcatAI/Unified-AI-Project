import pytest

# Import all agent classes to ensure they are discoverable and syntactically correct
from apps.backend.src.ai.agents.base.base_agent import BaseAgent
from apps.backend.src.ai.agents.audio_processing_agent import AudioProcessingAgent
from apps.backend.src.ai.agents.code_understanding_agent import CodeUnderstandingAgent
from apps.backend.src.ai.agents.creative_writing_agent import CreativeWritingAgent
from apps.backend.src.ai.agents.data_analysis_agent import DataAnalysisAgent

def test_import_base_agent():
    """Verify BaseAgent can be imported."""
    assert BaseAgent is not None

def test_import_audio_processing_agent():
    """Verify AudioProcessingAgent can be imported."""
    assert AudioProcessingAgent is not None

def test_import_code_understanding_agent():
    """Verify CodeUnderstandingAgent can be imported."""
    assert CodeUnderstandingAgent is not None

def test_import_creative_writing_agent():
    """Verify CreativeWritingAgent can be imported."""
    assert CreativeWritingAgent is not None

def test_import_data_analysis_agent():
    """Verify DataAnalysisAgent can be imported."""
    assert DataAnalysisAgent is not None
