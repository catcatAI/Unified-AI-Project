"""
Phase 1 Core Activation Tests — Context, Cycling, UnifiedLearning
Tests for DialogueContext, ModelContext, ToolContext, ED3N cycling, GARDEN cycling, UnifiedLearningOrchestrator
"""

from unittest.mock import MagicMock, patch

import pytest

# Lazy imports for optional modules
try:
    from ai.context.dialogue_context import DialogueContextManager
    from ai.context.model_context import ModelContextManager
    from ai.context.tool_context import ToolContextManager
    from ai.ed3n.ed3n_engine import ED3NEngine
    from ai.garden.garden_engine import GARDENEngine
    from ai.learning.unified_learning_orchestrator import UnifiedLearningOrchestrator
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Warning: Some imports not available: {e}")


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="Phase 1 modules not available"
)


class TestDialogueContext:
    """Tests for DialogueContextManager"""

    def test_initialization(self):
        mock_cm = MagicMock()
        dc = DialogueContextManager(mock_cm)
        assert dc is not None


class TestModelContext:
    """Tests for ModelContextManager"""

    def test_initialization(self):
        mock_cm = MagicMock()
        mc = ModelContextManager(mock_cm)
        assert mc is not None


class TestToolContext:
    """Tests for ToolContextManager"""

    def test_initialization(self):
        mock_cm = MagicMock()
        tc = ToolContextManager(mock_cm)
        assert tc is not None


class TestED3NCycling:
    """Tests for ED3N cycling behavior"""

    def test_initialization(self):
        engine = ED3NEngine()
        assert engine is not None

    def test_process_returns_string(self):
        engine = ED3NEngine()
        result = engine.process({"input": "What is AI?", "context": {}})
        assert result is not None
        assert isinstance(result, str)


class TestGARDENCycling:
    """Tests for GARDEN cycling behavior"""

    def test_initialization(self):
        engine = GARDENEngine()
        assert engine is not None

    def test_process_returns_string(self):
        engine = GARDENEngine()
        result = engine.process({"input": "What is AI?", "context": {}})
        assert result is not None
        assert isinstance(result, str)


class TestUnifiedLearningOrchestrator:
    """Tests for UnifiedLearningOrchestrator"""

    def test_initialization(self):
        orchestrator = UnifiedLearningOrchestrator()
        assert orchestrator is not None

    def test_has_learning_components(self):
        orchestrator = UnifiedLearningOrchestrator()
        assert hasattr(orchestrator, "_learning_orchestrator") or hasattr(
            orchestrator, "_continuous_learning"
        )

    def test_get_stats(self):
        orchestrator = UnifiedLearningOrchestrator()
        stats = orchestrator.get_stats()
        assert stats is not None
        assert isinstance(stats, dict)
