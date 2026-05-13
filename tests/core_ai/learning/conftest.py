import pytest

try:
    from ai.learning.content_analyzer_module import ContentAnalyzerModule
    CONTENT_ANALYZER_AVAILABLE = True
except ImportError:
    CONTENT_ANALYZER_AVAILABLE = False
    ContentAnalyzerModule = None


@pytest.fixture(scope="session")
def content_analyzer():
    """Create a ContentAnalyzerModule instance once for the entire test session."""
    if not CONTENT_ANALYZER_AVAILABLE:
        pytest.skip("ContentAnalyzerModule not available")
    return ContentAnalyzerModule()