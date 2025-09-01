import pytest
from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

@pytest.fixture(scope="session")
def content_analyzer():
    """Create a ContentAnalyzerModule instance once for the entire test session."""
    return ContentAnalyzerModule()