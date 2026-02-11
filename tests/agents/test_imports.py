import pytest

# Import all agent classes to ensure they are discoverable and syntactically correct
from ai.agents.base.base_agent import BaseAgent
from ai.agents.audio_processing_agent import AudioProcessingAgent
from ai.agents.code_understanding_agent import CodeUnderstandingAgent
from ai.agents.creative_writing_agent import CreativeWritingAgent
from ai.agents.data_analysis_agent import DataAnalysisAgent

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
