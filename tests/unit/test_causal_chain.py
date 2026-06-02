"""Tests for CausalChain and related types"""
import pytest


class TestCausalChain:
    """Tests for CausalChain dataclass"""

    def test_import_chain(self):
        """Verify CausalChain is importable and has expected methods"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        assert CausalChain is not None
        assert hasattr(CausalChain, 'add_node')
        assert hasattr(CausalChain, 'get_node')
        assert hasattr(CausalChain, 'get_children')
        assert hasattr(CausalChain, 'has_layer')
        assert hasattr(CausalChain, 'get_layer_nodes')
        assert hasattr(CausalChain, 'get_path_to_root')
        assert hasattr(CausalChain, 'get_execution_time')
        assert hasattr(CausalChain, 'to_dict')
        assert hasattr(CausalChain, 'from_dict')

    def test_instantiation(self):
        """Verify basic instantiation and node operations"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        instance = CausalChain(root_id="test-root")
        assert instance.root_id == "test-root"
        assert instance.nodes == []
        node = CausalNode(layer=LayerType.L2, module="test", action="process")
        instance.add_node(node)
        assert len(instance.nodes) == 1
        assert instance.get_node(node.id) is node
        assert instance.has_layer(LayerType.L2) is True
        assert instance.has_layer(LayerType.L1) is False
        assert instance.get_layer_nodes(LayerType.L2) == [node]

    def test_import_layer_type(self):
        """Verify LayerType enum values and from_string parsing"""
        from core.tracing.causal_chain import LayerType
        assert LayerType.L1.code == "L1"
        assert LayerType.L1.en_name == "Biological Layer"
        assert LayerType.L6.code == "L6"
        assert LayerType.L6.en_name == "Live2D Presentation Layer"
        assert str(LayerType.L3) == "L3"
        assert LayerType.from_string("L4") == LayerType.L4
        with pytest.raises(ValueError, match="Invalid layer"):
            LayerType.from_string("L99")

    def test_import_causal_node(self):
        """Verify CausalNode dataclass and its to_dict/from_dict round-trip"""
        from core.tracing.causal_chain import CausalNode, LayerType
        node = CausalNode(
            layer=LayerType.L3,
            module="identity",
            action="update",
            data={"key": "value"},
        )
        assert node.action == "update"
        assert node.module == "identity"
        assert node.layer == LayerType.L3
        assert node.data == {"key": "value"}
        d = node.to_dict()
        assert d["layer"] == "L3"
        assert d["action"] == "update"
        restored = CausalNode.from_dict(d)
        assert restored.id == node.id
        assert restored.layer == node.layer
        assert restored.action == node.action
        assert restored.data == node.data
