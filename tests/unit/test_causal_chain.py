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

    def test_get_children(self):
        """Verify get_children returns direct children"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="root")
        parent = CausalNode(layer=LayerType.L2, module="m", action="parent")
        child1 = CausalNode(layer=LayerType.L3, module="m", action="child1", parent_id=parent.id)
        child2 = CausalNode(layer=LayerType.L3, module="m", action="child2", parent_id=parent.id)
        unrelated = CausalNode(layer=LayerType.L4, module="m", action="orphan")
        for n in [parent, child1, child2, unrelated]:
            chain.add_node(n)
        children = chain.get_children(parent.id)
        assert len(children) == 2
        assert child1 in children
        assert child2 in children
        assert unrelated not in children
        assert chain.get_children("nonexistent") == []

    def test_get_path_to_root(self):
        """Verify get_path_to_root returns ancestor chain in order"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="root")
        n1 = CausalNode(layer=LayerType.L1, module="a", action="start")
        n2 = CausalNode(layer=LayerType.L2, module="b", action="process", parent_id=n1.id)
        n3 = CausalNode(layer=LayerType.L3, module="c", action="finish", parent_id=n2.id)
        for n in [n1, n2, n3]:
            chain.add_node(n)
        path = chain.get_path_to_root(n3.id)
        assert len(path) == 3
        assert path[0].id == n1.id
        assert path[1].id == n2.id
        assert path[2].id == n3.id

    def test_get_path_to_root_unknown_node(self):
        """Verify empty path for unknown node ID"""
        from core.tracing.causal_chain import CausalChain
        chain = CausalChain(root_id="root")
        assert chain.get_path_to_root("nonexistent") == []

    def test_get_execution_time(self):
        """Verify execution time calculation with multiple nodes"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        from datetime import datetime, timedelta
        chain = CausalChain(root_id="root")
        n1 = CausalNode(layer=LayerType.L1, module="a", action="start",
                        timestamp=datetime(2026, 1, 1, 0, 0, 0))
        n2 = CausalNode(layer=LayerType.L2, module="b", action="end",
                        timestamp=datetime(2026, 1, 1, 0, 0, 5))
        chain.add_node(n1)
        chain.add_node(n2)
        assert chain.get_execution_time() == 5.0

    def test_get_execution_time_single_node(self):
        """Verify execution time is 0 for single node"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="root")
        node = CausalNode(layer=LayerType.L1, module="a", action="start")
        chain.add_node(node)
        assert chain.get_execution_time() == 0.0

    def test_get_execution_time_empty(self):
        """Verify execution time is 0 for empty chain"""
        from core.tracing.causal_chain import CausalChain
        chain = CausalChain(root_id="root")
        assert chain.get_execution_time() == 0.0

    def test_chain_to_dict(self):
        """Verify CausalChain.to_dict serialization"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="test-root")
        node = CausalNode(layer=LayerType.L2, module="m", action="process")
        chain.add_node(node)
        d = chain.to_dict()
        assert d["root_id"] == "test-root"
        assert d["node_count"] == 1
        assert len(d["nodes"]) == 1
        assert d["nodes"][0]["layer"] == "L2"

    def test_chain_from_dict(self):
        """Verify CausalChain.from_dict deserialization"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="test-root")
        n1 = CausalNode(layer=LayerType.L1, module="a", action="start")
        n2 = CausalNode(layer=LayerType.L2, module="b", action="process", parent_id=n1.id)
        for n in [n1, n2]:
            chain.add_node(n)
        d = chain.to_dict()
        restored = CausalChain.from_dict(d)
        assert restored.root_id == "test-root"
        assert len(restored.nodes) == 2
        assert restored.get_node(n1.id) is not None
        assert restored.has_layer(LayerType.L2) is True

    def test_multiple_layers(self):
        """Verify has_layer detection across multiple nodes"""
        from core.tracing.causal_chain import CausalChain, CausalNode, LayerType
        chain = CausalChain(root_id="root")
        for lt in LayerType:
            chain.add_node(CausalNode(layer=lt, module="m", action="x"))
        assert chain.has_layer(LayerType.L1) is True
        assert chain.has_layer(LayerType.L6) is True
        assert chain.get_layer_nodes(LayerType.L3)[0].layer == LayerType.L3
        assert len(chain.get_layer_nodes(LayerType.L1)) == 1

    def test_get_node_not_found(self):
        """Verify get_node returns None for missing ID"""
        from core.tracing.causal_chain import CausalChain
        chain = CausalChain(root_id="root")
        assert chain.get_node("nonexistent") is None
