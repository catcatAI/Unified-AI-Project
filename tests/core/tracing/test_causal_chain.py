import pytest
from datetime import datetime, timedelta
from apps.backend.src.core.tracing.causal_chain import CausalNode, CausalChain, LayerType


class TestLayerType:
    def test_from_string_valid(self):
        assert LayerType.from_string("L1") == LayerType.L1
        assert LayerType.from_string("L6") == LayerType.L6

    def test_from_string_case_insensitive(self):
        assert LayerType.from_string("l3") == LayerType.L3

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            LayerType.from_string("L999")

    def test_str_representation(self):
        assert str(LayerType.L1) == "L1"

    def test_layer_properties(self):
        assert LayerType.L1.code == "L1"
        assert LayerType.L1.en_name == "Biological Layer"
        assert LayerType.L1.cn_name == "生物层"


class TestCausalNode:
    def test_auto_generates_id(self):
        node = CausalNode(module="test", action="execute")
        assert node.id is not None

    def test_to_dict(self):
        node = CausalNode(
            id="node_1", parent_id="root",
            layer=LayerType.L3, module="test_mod",
            action="run", data={"key": "val"},
        )
        d = node.to_dict()
        assert d["id"] == "node_1"
        assert d["parent_id"] == "root"
        assert d["layer"] == "L3"
        assert d["module"] == "test_mod"
        assert d["data"]["key"] == "val"
        assert "timestamp" in d

    def test_from_dict_roundtrip(self):
        original = CausalNode(
            id="node_1", parent_id="root",
            layer=LayerType.L4, module="m",
            action="a", data={"k": "v"},
        )
        d = original.to_dict()
        restored = CausalNode.from_dict(d)
        assert restored.id == original.id
        assert restored.parent_id == original.parent_id
        assert restored.layer == original.layer
        assert restored.module == original.module
        assert restored.action == original.action
        assert restored.data == original.data

    def test_from_dict_minimal(self):
        d = {
            "id": "n1", "layer": "L2",
            "timestamp": datetime.now().isoformat(),
        }
        node = CausalNode.from_dict(d)
        assert node.id == "n1"
        assert node.layer == LayerType.L2

    def test_default_timestamp(self):
        node = CausalNode(module="m", action="a")
        assert isinstance(node.timestamp, datetime)

    def test_default_layer(self):
        node = CausalNode(module="m", action="a")
        assert node.layer == LayerType.L1


class TestCausalChain:
    def test_create_chain(self):
        chain = CausalChain(root_id="root_1")
        assert chain.root_id == "root_1"
        assert len(chain.nodes) == 0

    def test_add_node(self):
        chain = CausalChain(root_id="root_1")
        node = CausalNode(module="m", action="a")
        chain.add_node(node)
        assert len(chain.nodes) == 1

    def test_get_node(self):
        chain = CausalChain(root_id="root_1")
        node = CausalNode(id="n1", module="m", action="a")
        chain.add_node(node)
        assert chain.get_node("n1") is node
        assert chain.get_node("nonexistent") is None

    def test_get_children(self):
        chain = CausalChain(root_id="root_1")
        parent = CausalNode(id="parent", module="m", action="a")
        child1 = CausalNode(id="c1", parent_id="parent", module="m", action="a")
        child2 = CausalNode(id="c2", parent_id="parent", module="m", action="a")
        unrelated = CausalNode(id="other", module="m", action="a")
        chain.add_node(parent)
        chain.add_node(child1)
        chain.add_node(child2)
        chain.add_node(unrelated)
        children = chain.get_children("parent")
        assert len(children) == 2
        assert all(c.id in ["c1", "c2"] for c in children)

    def test_has_layer(self):
        chain = CausalChain(root_id="root_1")
        chain.add_node(CausalNode(id="n1", layer=LayerType.L2, module="m", action="a"))
        assert chain.has_layer(LayerType.L2) is True
        assert chain.has_layer(LayerType.L5) is False

    def test_get_layer_nodes(self):
        chain = CausalChain(root_id="root_1")
        chain.add_node(CausalNode(id="n1", layer=LayerType.L2, module="m", action="a"))
        chain.add_node(CausalNode(id="n2", layer=LayerType.L2, module="m", action="a"))
        chain.add_node(CausalNode(id="n3", layer=LayerType.L5, module="m", action="a"))
        nodes = chain.get_layer_nodes(LayerType.L2)
        assert len(nodes) == 2

    def test_get_path_to_root(self):
        chain = CausalChain(root_id="root_1")
        root = CausalNode(id="root", module="r", action="start")
        child = CausalNode(id="child", parent_id="root", module="c", action="process")
        grandchild = CausalNode(id="gc", parent_id="child", module="g", action="finish")
        chain.add_node(root)
        chain.add_node(child)
        chain.add_node(grandchild)
        path = chain.get_path_to_root("gc")
        assert [n.id for n in path] == ["root", "child", "gc"]

    def test_get_execution_time_single_node(self):
        chain = CausalChain(root_id="root_1")
        node = CausalNode(module="m", action="a")
        chain.add_node(node)
        assert chain.get_execution_time() == 0.0

    def test_get_execution_time(self):
        chain = CausalChain(root_id="root_1")
        now = datetime.now()
        n1 = CausalNode(id="n1", module="m", action="a", timestamp=now)
        n2 = CausalNode(id="n2", parent_id="n1", module="m", action="b", timestamp=now + timedelta(seconds=5))
        chain.add_node(n1)
        chain.add_node(n2)
        assert chain.get_execution_time() == pytest.approx(5.0)

    def test_to_dict(self):
        chain = CausalChain(root_id="root_1")
        chain.add_node(CausalNode(id="n1", module="m", action="a"))
        d = chain.to_dict()
        assert d["root_id"] == "root_1"
        assert d["node_count"] == 1
        assert "created_at" in d

    def test_from_dict_roundtrip(self):
        chain = CausalChain(root_id="root_1")
        chain.add_node(CausalNode(id="n1", module="m", action="a", data={"k": "v"}))
        d = chain.to_dict()
        restored = CausalChain.from_dict(d)
        assert restored.root_id == chain.root_id
        assert len(restored.nodes) == len(chain.nodes)
        assert restored.nodes[0].id == chain.nodes[0].id
        assert restored.nodes[0].data == chain.nodes[0].data
