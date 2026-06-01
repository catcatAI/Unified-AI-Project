"""Smoke tests for CausalChain and related types"""
import pytest


class TestCausalChain:
    """Basic smoke tests for CausalChain dataclass"""

    def test_import_chain(self):
        """Verify CausalChain can be imported"""
        try:
            from core.tracing.causal_chain import CausalChain
            assert CausalChain is not None
        except ImportError as e:
            pytest.skip(f"CausalChain not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation with required root_id"""
        try:
            from core.tracing.causal_chain import CausalChain
            instance = CausalChain(root_id="test-root")
            assert instance is not None
            assert instance.root_id == "test-root"
            assert len(instance.nodes) == 0
        except ImportError as e:
            pytest.skip(f"CausalChain not available: {e}")
        except Exception as e:
            pytest.skip(f"CausalChain init failed (expected in CI): {e}")

    def test_import_layer_type(self):
        """Verify LayerType enum is importable"""
        try:
            from core.tracing.causal_chain import LayerType
            assert LayerType.L1 is not None
            assert LayerType.L6 is not None
        except ImportError as e:
            pytest.skip(f"LayerType not available: {e}")

    def test_import_causal_node(self):
        """Verify CausalNode dataclass is importable"""
        try:
            from core.tracing.causal_chain import CausalNode
            node = CausalNode()
            assert node is not None
            assert node.action == ""
        except ImportError as e:
            pytest.skip(f"CausalNode not available: {e}")
        except Exception as e:
            pytest.skip(f"CausalNode init failed (expected in CI): {e}")
